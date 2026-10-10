#include <stdio.h>
#include <string.h>
#include <deque>

using std::deque;

// -------------------------------------------------------------------------

char line[512];
unsigned char tile_map[16][2];

int last_ptr;

FILE *out_binary;
FILE *rom;

// -------------------------------------------------------------------------

int main( int argc, char** argv )
{
	if( strcmp(argv[1],"UNPACK")==0 )
	{
		int data_start, tile_stop;

		rom = fopen( argv[2], "rb" );
		out_binary = fopen( argv[3], "wb" );

		sscanf( argv[4], "%X", &data_start );
		sscanf( argv[5], "%X", &tile_stop );

		fseek( rom, data_start, SEEK_SET );

		// -----------------------------------------------------------------------
		// -----------------------------------------------------------------------

		int tile_types, tile_width, tile_height, tile_bytes;
		
		tile_types = fgetc(rom);
		tile_width = fgetc(rom);
		tile_height = fgetc(rom);
		tile_bytes = fgetc(rom);

		while( ftell(rom)<tile_stop )
		{
			int row, col, bitmaps;

			for( bitmaps=0; bitmaps<tile_types+1; bitmaps++ )
			{
				// init
				memset( tile_map, 0, sizeof(tile_map) );

				// tile height
				for( row=0; row<tile_height; row++ )
				{
					// tile width
					for( col=0; col<tile_width; col+=8 )
					{
						tile_map[row][col/8] = fgetc(rom);
					} // end tile width
				} // end tile height

				// dump TL,TR
				if(tile_height>0)
				{
					if(tile_width>0) for( row=0; row<8; row++ ) fputc( tile_map[row+0][0], out_binary );
					if(tile_width>8) for( row=0; row<8; row++ ) fputc( tile_map[row+0][1], out_binary );
				}
				
				// dump BL,BR
				if(tile_height>8)
				{
					if(tile_width>0) for( row=0; row<8; row++ ) fputc( tile_map[row+8][0], out_binary );
					if(tile_width>8) for( row=0; row<8; row++ ) fputc( tile_map[row+8][1], out_binary );
				}
			}
		} // end font

		if( out_binary ) fclose(out_binary);
		if( rom ) fclose(rom);
	}

	// -------------------------------------------------------------
	// *************************************************************
	// -------------------------------------------------------------

	if( strcmp(argv[1],"REPACK")==0 )
	{
		int data_start, tile_stop;

		rom = fopen( argv[2], "rb+" );
		out_binary = fopen( argv[3], "rb" );

		sscanf( argv[4], "%X", &data_start );
		sscanf( argv[5], "%X", &tile_stop );

		fseek( rom, data_start, SEEK_SET );

		// ----------------------------------------------------------------
		// ----------------------------------------------------------------

		int tile_types, tile_width, tile_height, tile_bytes;
		int ptr;
		
		tile_types = fgetc(rom);
		tile_width = fgetc(rom);
		tile_height = fgetc(rom);
		tile_bytes = fgetc(rom);
		ptr = ftell(rom);

		while( ftell(rom)<tile_stop )
		{
			int row, col, bitmaps;

			// strange workaround (stops writing after $1000 bytes)
			fseek( rom, ptr, SEEK_SET );

			for( bitmaps=0; bitmaps<tile_types+1; bitmaps++ )
			{
				// init
				memset( tile_map, 0, sizeof(tile_map) );

				// load TL,TR
				if(tile_height>0)
				{
					if(tile_width>0) for( row=0; row<8; row++ ) tile_map[row+0][0] = fgetc(out_binary);
					if(tile_width>8) for( row=0; row<8; row++ ) tile_map[row+0][1] = fgetc(out_binary);
				}
				
				// load BL,BR
				if(tile_height>8)
				{
					if(tile_width>0) for( row=0; row<8; row++ ) tile_map[row+8][0] = fgetc(out_binary);
					if(tile_width>8) for( row=0; row<8; row++ ) tile_map[row+8][1] = fgetc(out_binary);
				}

				// tile height
				for( row=0; row<tile_height; row++ )
				{
					// tile width
					for( col=0; col<tile_width; col+=8 )
					{
						fputc( tile_map[row][col/8], rom );
					} // end tile width
				} // end tile height
			}

			ptr = ftell(rom);
		} // end font

		if( out_binary ) fclose(out_binary);
		if( rom ) fclose(rom);
	}

	// -------------------------------------------------------------
	// *************************************************************
	// -------------------------------------------------------------

	return 0;
}