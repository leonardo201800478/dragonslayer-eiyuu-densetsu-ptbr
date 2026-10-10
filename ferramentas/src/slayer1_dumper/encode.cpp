/*
Sylvan Tale: LZ compression (basis)
*/

#include <stdio.h>

#include <stdio.h>
#include <stdlib.h>
#include <memory.h>

#include <vector>
#include <deque>

using namespace std;

typedef struct
{
	int pos;
	int ptr;
	int len;
} lz_find;


//#define DEBUG_LZ

//unsigned char buffer[0x4000];

//unsigned char out_buffer[0x10000];
//int buf_ptr;

///////////////////////////////////////////////////////

vector<int> table[256];
deque<lz_find> lz_table;

int ptr = 0;
int size = 0;

int max_runs = 0;
int max_delta = 0;

int LZ_min_match = 1+1;
int LZ_window_size = 0x2000-1;				// 13-bits
int LZ_max_match = (0x100-1)+0xd+1;		// 8-bits + DBFa

//#define ALLOW_RLE 0
#define ALLOW_RLE 1

int RLE_min_match = 0xd+1;
int RLE_window_size = 1;							// LZ --> RLE
int RLE_max_match = (0x1000-1)+0xd+1;	// 12-bits + DBFa


void Find_LZ( int start, unsigned char byte, int &length, int &pos )
{
	int longest_length = 0;
	int longest_ptr = 0;

	// use cached positions to quickly look through the file
	for( int lcv = 0; lcv < table[ byte ].size(); lcv++ ) {
		int match_length = 0;
		int ptr = table[ byte ][ lcv ];
		int stop;

		// invalid string; stop scanning
		if( ptr >= start )
			break;

		// LZ window restriction
		if( start - ptr > LZ_window_size )
			continue;

		if( (start-ptr)==1 && ALLOW_RLE )
		{
			// pseudo-RLE detection
			stop = start + RLE_max_match + RLE_min_match;
		}
		else
		{
			// LZ detection
			stop = start + LZ_max_match + LZ_min_match;
		}

		// search for longest identical substring
		for( int lcv2 = start; (lcv2<=stop) && (lcv2<size); lcv2++ )
		{
			// look for a mismatch
			if( buffer[ lcv2 ] != buffer[ ptr ] )
				break;

			// keep looking
			ptr++;
			match_length++;
		}

		// record new long find
		if( longest_length <= match_length ) {
			longest_ptr = table[ byte ][ lcv ];
			longest_length = match_length;
		}
	}

	// output findings
	length = longest_length;
	pos = longest_ptr;
}

///////////////////////////////////////////////////////
///////////////////////////////////////////////////////

void LZ_Encode( FILE *in, FILE *out )
{
	lz_find lz;
	int start;
	int lcv;
	int counter = 0;

	// Step 0: Check file size
	fread( buffer, 1, 0x10000, in );
	size = ftell( in );
	fseek( in, 0, SEEK_SET );

	// init
	for( lcv=0; lcv<256; lcv++ )
		table[lcv].erase( table[lcv].begin(), table[lcv].end() );
	lz_table.erase( lz_table.begin(), lz_table.end() );


	////////////////////////////////////////////////

	// Step 1: Find all LZ matches

	start = 0;
	while( start < size )
	{
		int future_length[1];
		int future_pos[1];

		int length;
		int pos;

		// Prepare for LZ
		table[ buffer[ start ] ].push_back( start );

		// Go find the longest substring match (and future ones)
		Find_LZ( start, buffer[ start ], length, pos );

		// Slightly increase ratio performance
#define LOOK 1
		for( lcv=0; lcv<LOOK; lcv++)
		{
			start++; table[ buffer[ start ] ].push_back( start );
			Find_LZ( start, buffer[ start ], future_length[ lcv ], future_pos[ lcv ]);
		}

		// Un-do lookahead
		for( lcv=LOOK; lcv>0; lcv-- )
		{
			table[ buffer[ start ] ].pop_back(); start--;
			if( future_length[ lcv-1 ] - length >= lcv )
				length = 0;
		}

		if( length >= LZ_min_match )
		{
			// copy saturation (break into two GUARANTEED matches)
			if( ALLOW_RLE && start-pos==1 && length>RLE_max_match )
				length = RLE_max_match - RLE_min_match;
			else if( length>LZ_max_match )
				length = LZ_max_match - LZ_min_match;

			// Found substring match; record and re-do
			lz.pos = start;
			lz.ptr = start - pos;
			lz.len = length;

			lz_table.push_back( lz );

			// Need to add to LZ table
			for( int lcv = 1; lcv < length; lcv++ )
				table[ buffer[ start + lcv ] ].push_back( start + lcv );

			// Fast update
			start += length;
		}
		else
		{
			// No substrings found; try again
			start++;
		}
	}

	// insert dummy entry
	lz.pos = -1;
	lz_table.push_back( lz );

///////////////////////////////////////////////////////////////

	int lz_ptr;
	int out_byte;
	int out_bits;

	int out_ptr;
	int out_size;
	bool first;

	// init
	lz_ptr = 0;
	start = 0;
	out_ptr = 0;

	out_byte = 0;
	out_bits = 8;
	out_size = 0;

	first = true;

// yuck!
#define SHIFT_BARREL(BIT) \
	{ \
		if( !out_bits ) \
		{ \
			if( first ) \
			{ \
				out_byte >>= 8; \
				first = false; \
				\
				fputc( (out_byte>>8)&0xff, out ); \
				fputc( (out_byte>>0)&0xff, out ); \
			} \
			else \
			{ \
				fputc( (out_byte>>0)&0xff, out ); \
				fputc( (out_byte>>8)&0xff, out ); \
			} \
			\
			fwrite( out_buffer, 1, out_ptr, out ); \
			\
			out_size += 2; \
			out_size += out_ptr; \
			\
			out_ptr = 0; \
			out_byte = 0; \
			out_bits = 16; \
		} \
		out_byte >>= 1; \
		out_byte |= ( BIT << 15 ); \
		out_bits--; \
	}


	// Step 2: Prepare encoding methods
	while( start < size )
	{
		int lcv;

		lz = lz_table[ lz_ptr ];

		// debug
		//if(start>=0x4fe0)
			//lcv=0;

		if( lz.pos==start )
		{
			start += lz.len;

			// LZ or RLE
			SHIFT_BARREL(1);

			// ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

			if( lz.ptr==1 && lz.len>=RLE_min_match )
			{
				// RLE detection
				SHIFT_BARREL(1);

				// RLE window ptr
				for( lcv=12; lcv>=8; lcv-- )
				{
					SHIFT_BARREL(0);
				}
				out_buffer[ out_ptr++ ] = 1;

				// RLE run amount
				lz.len -= (0xd+1);
				if(lz.len<16)
				{
					// no extend
					SHIFT_BARREL(0);

					for( lcv=3; lcv>=0; lcv-- )
					{
						int bit;

						bit = lz.len & (1<<lcv);
						bit >>= lcv;
						SHIFT_BARREL(bit);
					}
				}
				else
				{
					// extend
					SHIFT_BARREL(1);

					for( lcv=3+8; lcv>=0+8; lcv-- )
					{
						int bit;

						bit = lz.len & (1<<lcv);
						bit >>= lcv;
						SHIFT_BARREL(bit);
					}

					// add remaining run
					out_buffer[ out_ptr++ ] = lz.len&0xff;
				}

				// add RLE byte
				out_buffer[ out_ptr++ ] = buffer[lz.pos-1];

				lz_ptr++;
				continue;
			}

			// ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

			if( lz.ptr<256 )
			{
				// LZ-8
				SHIFT_BARREL(0);
				out_buffer[ out_ptr++ ] = lz.ptr & 0xff;
			}
			else
			{
				// LZ-13
				SHIFT_BARREL(1);
				for( lcv=12; lcv>=8; lcv-- )
				{
					int bit;

					bit = lz.ptr & (1<<lcv);
					bit >>= lcv;
					SHIFT_BARREL(bit);
				}
				out_buffer[ out_ptr++ ] = lz.ptr&0xff;
			}

			// LZ run
			if( lz.len==1+1 ) { SHIFT_BARREL(1); lz_ptr++; continue; }
			SHIFT_BARREL(0);

			if( lz.len==2+1 ) { SHIFT_BARREL(1); lz_ptr++; continue; }
			SHIFT_BARREL(0);

			if( lz.len==3+1 ) { SHIFT_BARREL(1); lz_ptr++; continue; }
			SHIFT_BARREL(0);

			if( lz.len==4+1 ) { SHIFT_BARREL(1); lz_ptr++; continue; }
			SHIFT_BARREL(0);

			if( lz.len-(5+1) < 8 )
			{
				SHIFT_BARREL(1);

				lz.len -= (5+1);
				for( lcv=2; lcv>=0; lcv-- )
				{
					int bit;

					bit = lz.len & (1<<lcv);
					bit >>= lcv;
					SHIFT_BARREL(bit);
				}
			}
			else //if( lz.len-(0xd+1) < 256 )
			{
				SHIFT_BARREL(0);

				lz.len -= (0xd+1);
				out_buffer[ out_ptr++ ] = lz.len & 0xff;
			}

			lz_ptr++;
			continue;
		}
		else
		{
			// Free byte
			SHIFT_BARREL(0);

			out_buffer[ out_ptr++ ] = buffer[ start ];
			start++;
		}
	} // end method check

	// add termination code
	SHIFT_BARREL(1);
	SHIFT_BARREL(1);

	// window = 0
	for( lcv=12; lcv>=8; lcv-- )
		SHIFT_BARREL(0);

	// shove in dummy bits = FLUSH
	for( lcv=out_bits; lcv>=0; lcv-- )
	{
		SHIFT_BARREL(0);
	}

	// LZ-13
	fputc( 0,out );
	out_size++;

	// stop byte
	fputc( 0,out );
	out_size++;


	// Step 2.5:
	// - WORD alignment
	if( ((out_size+0)%2)==1 ) fputc( 0,out );
}
