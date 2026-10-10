#define READ_BUFFER_CACHE

#define BUFFER_MAX 0x10000

int BUFFER_SIZE;
unsigned char buffer[BUFFER_MAX];

//#define NO_KANJI


unsigned int GetMSBAddress(unsigned int Offset, int size)
{
	// 16-bit MSB
	if( size == 16 )
	{
		return
			( ( Offset&0xff00 ) >> 8 ) |
			( ( Offset&0x00ff ) << 8 );
	}

	// 24-bit MSB
	if( size == 24 )
	{
		return
			( ( Offset&0xff0000 ) >> 16 ) |
			( ( Offset&0x00ff00 ) >> 0 ) |
			( ( Offset&0x0000ff ) << 16 );
	}

	// 32-bit MSB
	return
		( ( Offset&0xff000000 ) >> 24 ) |
		( ( Offset&0x00ff0000 ) >> 8 ) |
		( ( Offset&0x0000ff00 ) << 8 ) |
		( ( Offset&0x000000ff ) << 24 );
}


void Cache_Buffer( int offset, FILE *fp = rom )
{
	fseek( fp,offset,SEEK_SET );
	
	BUFFER_SIZE = fread( buffer, 1, BUFFER_MAX, fp );
	buffer_ptr = 0;
}

// ------------------------------------------------------------------
// ------------------------------------------------------------------

unsigned char Peek_Byte( int num, int skip_byte=0 )
{
	int value, ptr;

	if(!num) return -1;

#ifdef READ_BUFFER_CACHE
	ptr = buffer_ptr;
	buffer_ptr += skip_byte;

	while( num-- )
	{
		if(buffer_ptr>=BUFFER_SIZE) return -1;
		value = buffer[ buffer_ptr++ ];
	}

	buffer_ptr = ptr;
#else
	ptr = ftell(rom);
	while( skip_byte-- ) fgetc(rom);

	while( num-- )
	{
		value = fgetc(rom);
	}

	fseek( rom,ptr,SEEK_SET );
#endif

	return value;
}


unsigned char Read_Byte( int num )
{
	int value;

	if(!num) return -1;

#ifdef READ_BUFFER_CACHE
	while( num-- )
	{
		if(buffer_ptr>=BUFFER_SIZE) return -1;
		value = buffer[ buffer_ptr++ ];
	}
#else
	while( num-- )
	{
		value = fgetc(rom);
	}
#endif

	return value;
}

// ------------------------------------------------------------------
// ------------------------------------------------------------------

unsigned short Read_Word( int num )
{
	int value;

	if(!num) return -1;

#ifdef READ_BUFFER_CACHE
	while( num-- )
	{
		if(buffer_ptr>=BUFFER_SIZE) return -1;
		value = (buffer[ buffer_ptr++ ])<<0;

		if(buffer_ptr>=BUFFER_SIZE) return -1;
		value |= (buffer[ buffer_ptr++ ])<<8;
	}
#else
	while( num-- )
	{
		value = fgetc(rom)<<0;
		value |= fgetc(rom)<<8;
	}
#endif

#ifdef MSB
	value = GetMSBAddress( value,16 );
#endif

	return value;
}


unsigned short Peek_Word( int num, int skip_byte=0 )
{
	int value, ptr;

	if(!num) return -1;

#ifdef READ_BUFFER_CACHE
	ptr = buffer_ptr;
	buffer_ptr += skip_byte;
	while( num-- )
	{
		if(buffer_ptr>=BUFFER_SIZE) return -1;
		value = (buffer[ buffer_ptr++ ])<<0;

		if(buffer_ptr>=BUFFER_SIZE) return -1;
		value |= (buffer[ buffer_ptr++ ])<<8;
	}
	buffer_ptr = ptr;
#else
	ptr = ftell(rom);
	while( skip_byte-- ) fgetc(rom);
	while( num-- )
	{
		value = fgetc(rom)<<0;
		value |= fgetc(rom)<<8;
	}
	fseek( rom,ptr,SEEK_SET );
#endif

#ifdef MSB
	value = GetMSBAddress( value,16 );
#endif

	return value;
}

// ------------------------------------------------------------------
// ------------------------------------------------------------------

unsigned int Read_Tribyte( int num )
{
	int value;

	if(!num) return -1;

#ifdef READ_BUFFER_CACHE
	while( num-- )
	{
		if(buffer_ptr>=BUFFER_SIZE) return -1;
		value = (buffer[ buffer_ptr++ ])<<0;

		if(buffer_ptr>=BUFFER_SIZE) return -1;
		value |= (buffer[ buffer_ptr++ ])<<8;

		if(buffer_ptr>=BUFFER_SIZE) return -1;
		value |= (buffer[ buffer_ptr++ ])<<16;
	}
#else
	while( num-- )
	{
		value = fgetc(rom)<<0;
		value |= fgetc(rom)<<8;
		value |= fgetc(rom)<<16;
	}
#endif

#ifdef MSB
	value = GetMSBAddress( value,24 );
#endif

	return value;
}


unsigned int Peek_Tribyte( int num, int skip_byte=0 )
{
	int value, ptr;

	if(!num) return -1;

#ifdef READ_BUFFER_CACHE
	ptr = buffer_ptr;
	buffer_ptr += skip_byte;
	while( num-- )
	{
		if(buffer_ptr>=BUFFER_SIZE) return -1;
		value = (buffer[ buffer_ptr++ ])<<0;

		if(buffer_ptr>=BUFFER_SIZE) return -1;
		value |= (buffer[ buffer_ptr++ ])<<8;

		if(buffer_ptr>=BUFFER_SIZE) return -1;
		value |= (buffer[ buffer_ptr++ ])<<16;
	}
	buffer_ptr = ptr;
#else
	ptr = ftell(rom);
	while( skip_byte-- ) fgetc(rom);
	while( num-- )
	{
		value = fgetc(rom)<<0;
		value |= fgetc(rom)<<8;
		value |= fgetc(rom)<<16;
	}
	fseek( rom,ptr,SEEK_SET );
#endif

#ifdef MSB
	value = GetMSBAddress( value,24 );
#endif

	return value;
}

// ------------------------------------------------------------------
// ------------------------------------------------------------------

unsigned int Read_Dword( int num )
{
	int value;

	if(!num) return -1;

#ifdef READ_BUFFER_CACHE
	while( num-- )
	{
		if(buffer_ptr>=BUFFER_SIZE) return -1;
		value = (buffer[ buffer_ptr++ ])<<0;

		if(buffer_ptr>=BUFFER_SIZE) return -1;
		value |= (buffer[ buffer_ptr++ ])<<8;

		if(buffer_ptr>=BUFFER_SIZE) return -1;
		value |= (buffer[ buffer_ptr++ ])<<16;

		if(buffer_ptr>=BUFFER_SIZE) return -1;
		value |= (buffer[ buffer_ptr++ ])<<24;
	}
#else
	while( num-- )
	{
		value = fgetc(rom)<<0;
		value |= fgetc(rom)<<8;
		value |= fgetc(rom)<<16;
		value |= fgetc(rom)<<24;
	}
#endif

#ifdef MSB
	value = GetMSBAddress( value,32 );
#endif

	return value;
}


unsigned int Peek_Dword( int num )
{
	int value, ptr;

	if(!num) return -1;

#ifdef READ_BUFFER_CACHE
	ptr = buffer_ptr;
	while( num-- )
	{
		if(buffer_ptr>=BUFFER_SIZE) return -1;
		value = (buffer[ buffer_ptr++ ])<<0;

		if(buffer_ptr>=BUFFER_SIZE) return -1;
		value |= (buffer[ buffer_ptr++ ])<<8;

		if(buffer_ptr>=BUFFER_SIZE) return -1;
		value |= (buffer[ buffer_ptr++ ])<<16;

		if(buffer_ptr>=BUFFER_SIZE) return -1;
		value |= (buffer[ buffer_ptr++ ])<<24;
	}
	buffer_ptr = ptr;
#else
	ptr = ftell(rom);
	while( num-- )
	{
		value = fgetc(rom)<<0;
		value |= fgetc(rom)<<8;
		value |= fgetc(rom)<<16;
		value |= fgetc(rom)<<24;
	}
	fseek( rom,ptr,SEEK_SET );
#endif

#ifdef MSB
	value = GetMSBAddress( value,32 );
#endif

	return value;
}

// ------------------------------------------------------------------
// ------------------------------------------------------------------

unsigned char Print_Byte( int num )
{
	int value;

	if(!num) return -1;

#ifdef READ_BUFFER_CACHE
	while( num-- )
	{
		value = buffer[ buffer_ptr++ ];
		fprintf( out_text, "<$%02X>", value );
	}
#else
	while( num-- )
	{
		value = fgetc(rom);
		fprintf( out_text, "<$%02X>", value );
	}
#endif

	return value;
}

// ===================================================================
// *******************************************************************
// *******************************************************************
// ===================================================================

int args_table[] =
{
	0,0,0,0,		// 00-03
	0,0,0,0,		// 04-07
	0,1,0,0,		// 08-0B
	2,0,0,2,		// 0C-0F

	2,2,2,2,		// 10-13
	2,2,10,0,		// 14-17
	0,0,0,0,		// 18-1B
	0,0,0,0,		// 1C-1F

	0,0,0,0,		// E0-E3
	0,0,0,0,		// E4-E7
	0,0,0,0,		// E8-EB (EB+)
	0,4,1,1,		// EC-EF

	1,1,2,2,		// F0-F3
	3,0,2,0,		// F4-F7
	3,3,0,0,		// F8-FB
	1,1,1,1,		// FC-FF
};

short args_code[256];

deque<int> ptr_list;


unsigned char mark_rom[0x20 * 0x10000];
int mark_index;

int EMBED_COUNT;
int text_stop;

int last_code;
int last_stop;
int jmp_cond;

int LAST_DUMP;

int WRITE_ROM;
int WRITE_SIZE;
int WRITE_START;

#define TYPE_NONE 0x00
#define TYPE_CODE 0x01
#define TYPE_PASS1 0x02
#define TYPE_PASS2 0x04
#define TYPE_PASS3 0x08
#define TYPE_DIRTY 0x80

// -------------------------------------------------------------------
// -------------------------------------------------------------------

// code flow hacks - do not dump
#define SKIP_HACKS \
		if( file_no==0x3c && buffer_ptr==0x351 ) return; \
		if( file_no==0x62 && buffer_ptr==0xad8 ) return; \
		if( file_no==0x64 && buffer_ptr==0x5bd ) return; \
		if( file_no==0x66 && buffer_ptr==0x843 ) return; \
		if( file_no==0x6e && buffer_ptr==0x7a6 ) return; \
		if( file_no==0x89 && buffer_ptr==0xd66 ) return; \
		if( file_no==0x8a && buffer_ptr==0x12db ) return; \
		if( file_no==0x95 && buffer_ptr==0xec4 ) return; \
		if( file_no==0x9f && buffer_ptr==0xb88 ) return; \
		if( file_no==0xa5 && buffer_ptr==0x128d ) return; \
		if( file_no==0xbf && buffer_ptr==0x4f5 ) return; \
		if( file_no==0xc0 && buffer_ptr==0xc19 ) return; \
		if( file_no==0xc3 && buffer_ptr==0xf99 ) return; \
		if( file_no==0xca && buffer_ptr==0xd59 ) return; \
		if( file_no==0xcb && buffer_ptr==0x1143 ) return; \
		if( file_no==0xcf && buffer_ptr==0xc4a ) return; \
		if( file_no==0xdb && buffer_ptr==0xf6d ) return; \
		if( file_no==0xdd && buffer_ptr==0x11a4 ) return; \
		if( file_no==0xde && buffer_ptr==0xcc9 ) return; \
		if( file_no==0xdf && buffer_ptr==0x543 ) return; \


// code flow hacks - more text probably follows
#define DUMP_HACKS \
		if( file_no==0x01 && buffer_ptr==0x7dc ) goto dump_string; \
		if( file_no==0x03 && buffer_ptr==0x5ae ) goto dump_string; \
		if( file_no==0x04 && buffer_ptr==0x5ec ) goto dump_string; \
		if( file_no==0x07 && buffer_ptr==0x776 ) goto dump_string; \
		if( file_no==0x08 && buffer_ptr==0x6de ) goto dump_string; \
		if( file_no==0x09 && buffer_ptr==0x928 ) goto dump_string; \
		if( file_no==0x0a && buffer_ptr==0x940 ) goto dump_string; \
		if( file_no==0x0c && buffer_ptr==0x7a8 ) goto dump_string; \
		if( file_no==0x0e && buffer_ptr==0x84e ) goto dump_string; \
		if( file_no==0x11 && buffer_ptr==0x589 ) goto dump_string; \
		if( file_no==0x15 && buffer_ptr==0x1414 ) goto dump_string; \
		if( file_no==0x16 && buffer_ptr==0x284 ) goto dump_string; \
		if( file_no==0x18 && buffer_ptr==0x4cf ) goto dump_string; \
		if( file_no==0x1a && buffer_ptr==0x236 ) goto dump_string; \
		if( file_no==0x1e && buffer_ptr==0x2c6 ) goto dump_string; \
		if( file_no==0x23 && buffer_ptr==0x5f5 ) goto dump_string; \
		if( file_no==0x26 && buffer_ptr==0x469 ) goto dump_string; \
		if( file_no==0x2a && buffer_ptr==0x3ca ) goto dump_string; \
		if( file_no==0x2c && buffer_ptr==0x450 ) goto dump_string; \
		if( file_no==0x2c && buffer_ptr==0x882 ) goto dump_string; \
		if( file_no==0x2d && buffer_ptr==0x49f ) goto dump_string; \
		if( file_no==0x32 && buffer_ptr==0x44f ) goto dump_string; \
		if( file_no==0x32 && buffer_ptr==0x45f ) goto dump_string; \
		if( file_no==0x37 && buffer_ptr==0x202 ) goto dump_string; \
		if( file_no==0x38 && buffer_ptr==0x853 ) goto dump_string; \
		if( file_no==0x3f && buffer_ptr==0xfc4 ) goto dump_string; \
		if( file_no==0x40 && buffer_ptr==0x906 ) goto dump_string; \
		if( file_no==0x41 && buffer_ptr==0xbf0 ) goto dump_string; \
		if( file_no==0x42 && buffer_ptr==0x8b6 ) goto dump_string; \
		if( file_no==0x43 && buffer_ptr==0x368 ) goto dump_string; \
		if( file_no==0x44 && buffer_ptr==0x3c6 ) goto dump_string; \
		if( file_no==0x45 && buffer_ptr==0x757 ) goto dump_string; \
		if( file_no==0x46 && buffer_ptr==0x58a ) goto dump_string; \
		if( file_no==0x47 && buffer_ptr==0x643 ) goto dump_string; \
		if( file_no==0x48 && buffer_ptr==0x40c ) goto dump_string; \
		if( file_no==0x4d && buffer_ptr==0x13a5 ) goto dump_string; \
		if( file_no==0x4e && buffer_ptr==0xe1e ) goto dump_string; \
		if( file_no==0x4f && buffer_ptr==0x5c3 ) goto dump_string; \
		if( file_no==0x57 && buffer_ptr==0x380 ) goto dump_string; \
		if( file_no==0x60 && buffer_ptr==0x352 ) goto dump_string; \
		if( file_no==0x61 && buffer_ptr==0x2cc ) goto dump_string; \
		if( file_no==0x62 && buffer_ptr==0x3fa ) goto dump_string; \
		if( file_no==0x63 && buffer_ptr==0x2e8 ) goto dump_string; \
		if( file_no==0x78 && buffer_ptr==0x29f ) goto dump_string; \
		if( file_no==0x7f && buffer_ptr==0x575 ) goto dump_string; \
		if( file_no==0x80 && buffer_ptr==0x6b5 ) goto dump_string; \
		if( file_no==0x81 && buffer_ptr==0x5d1 ) goto dump_string; \
		if( file_no==0x82 && buffer_ptr==0x553 ) goto dump_string; \
		if( file_no==0x82 && buffer_ptr==0x6f9 ) goto dump_string; \
		if( file_no==0x83 && buffer_ptr==0x537 ) goto dump_string; \
		if( file_no==0x83 && buffer_ptr==0x600 ) goto dump_string; \
		if( file_no==0x83 && buffer_ptr==0x7d9 ) goto dump_string; \
		if( file_no==0xae && buffer_ptr==0x8a4 ) goto dump_string; \
		if( file_no==0xaf && buffer_ptr==0x830 ) goto dump_string; \
		if( file_no==0xb0 && buffer_ptr==0x830 ) goto dump_string; \
		if( file_no==0xb3 && buffer_ptr==0x54c ) goto dump_string; \
		if( file_no==0xb3 && buffer_ptr==0xfa7 ) { buffer_ptr=0xfaf; goto dump_string; } \
		if( file_no==0xb5 && buffer_ptr==0x3ee ) goto dump_string; \
		if( file_no==0xb7 && buffer_ptr==0x328 ) goto dump_string; \
		if( file_no==0xc0 && buffer_ptr==0x403 ) goto dump_string; \
		if( file_no==0xc1 && buffer_ptr==0x37f ) goto dump_string; \
		if( file_no==0xc2 && buffer_ptr==0x6d9 ) goto dump_string; \
		if( file_no==0xc5 && buffer_ptr==0x146d ) goto dump_string; \
		if( file_no==0xc7 && buffer_ptr==0x6b2 ) goto dump_string; \
		if( file_no==0xca && buffer_ptr==0x418 ) goto dump_string; \
		if( file_no==0xca && buffer_ptr==0x12db ) goto dump_string; \
		if( file_no==0xd9 && buffer_ptr==0x609 ) goto dump_string; \
		if( file_no==0xdd && buffer_ptr==0xf04 ) goto dump_string; \


void Dump_Layer3( int start_offset, int pass=0, int file_no=0 )
{
	int file_ptr, base;

	buffer_ptr = start_offset;

	// dumper start
	if( pass==0 )
	{
		// read data
		Cache_Buffer( start_offset );
		base = start_offset;

		// init
		file_ptr = 0;
		last_stop = 0;
		jmp_cond = 0;

		WRITE_ROM = 0;
		WRITE_SIZE = 0;

		//memset( mark_rom, 0, sizeof(mark_rom) );

		// -------------------------------------------------------------------------

		// safety check
		if( (mark_rom[ base+buffer_ptr ] & TYPE_DIRTY) )
		{
			return;
		}
		mark_rom[ base+buffer_ptr ] |= TYPE_DIRTY;

		if( LAST_DUMP > start_offset )
		{
			printf( "\n[DUMP] FAIL-SAFE REWIND @ %04X", start_offset );
		}
		LAST_DUMP = base + buffer_ptr;

		// Atlas header
		fprintf( out_text, "\n//[%06X]", base+buffer_ptr );
		fprintf( out_text, "\n\n//" );
	}

	// -------------------------------------------------------------------------
	// -------------------------------------------------------------------------

	// dump string
	while(1)
	{
		int code;
		bool EXIT;

		// ptr state CHECK (don't duplicate data)
		EXIT = false;
		if( base+buffer_ptr > start_offset )
		{
			if( mark_rom[ base+buffer_ptr ] & TYPE_PASS2 )
			{
				EXIT = true;
				goto turn_off_ROM;
			}
		}

		// ------------------------------------------------------------------------
		// ------------------------------------------------------------------------

		// Read script
		code = Read_Byte(1);
		last_code = code;

		// ------------------------------------------------------------------------
		// ------------------------------------------------------------------------

		if( pass==0 )
		{
			// opcodes to turn ON ROM WRITING
			if(
				code==0x02 ||
				code==0x0B ||	code==0x0E ||
				code==0x10 || code==0x16 ||
				(code>=0x20 && code<=0xeb) )
			{
				// no text checks - NO INLINE
				if( start_offset==0x24a66 )
				{
					WRITE_ROM=0;
				}


				// turn ON check
				else if( WRITE_ROM==0 )
				{
					WRITE_ROM = 1;
					WRITE_SIZE = 0;
					WRITE_START = buffer_ptr+2;

					// mark ROM
					fprintf( out_text, "\n" );
					fprintf( out_text, "\n#WRITE(PtrTable)" );
					fprintf( out_text, "\n#W08BYTE($%X, $EB)", base+buffer_ptr-1, base_name );
					fprintf( out_text, "\n#WRITEINDEX($%X, 2)", base+buffer_ptr+0, base_name );
					fprintf( out_text, "\n" );
					fprintf( out_text, "\n" );
				}

				// ALREADY ON
			}


			// IGNORE opcodes
			else if(
				code==0x01 || code==0x03 || code==0x04 || code==0x05 || code==0x08 || code==0x09 ||
				code==0x0C ||	code==0x13 ||	code==0x14 ||
				code==0x18 ||	code==0x19 ||	code==0x1A ||
				code==0x1B || code==0x1C || code==0x1D ||	code==0x1E ||	code==0x1F )
			{}


			// remaining opcodes to turn OFF ROM WRITING
			else if( WRITE_ROM==1 )
			{
				int old_ptr;

turn_off_ROM:
				if( WRITE_ROM==0 ) break;

				WRITE_ROM = 0;
				old_ptr = buffer_ptr;


				// special case - index WARN hacks (3-byte space issue)
				if(0) {}
				else if( file_no==0x15 && buffer_ptr==0x1715+1 )
				{
					// Rewire JMP code (use DIRECT JMP.L)
					buffer_ptr = 0x171c;

					WRITE_SIZE = 3;
				}
				else if( file_no==0x15 && buffer_ptr==0x1769+1 )
				{
					// Rewire JMP code (use DIRECT JMP.L)
					buffer_ptr = 0x1770;

					WRITE_SIZE = 3;
				}
				else if( file_no==0x15 && buffer_ptr==0x17cd+1 )
				{
					// Rewire JMP code (use DIRECT JMP.L)
					buffer_ptr = 0x17d4;

					WRITE_SIZE = 3;
				}
				else if( EXIT==0 )
					buffer_ptr--;


				// adjust to ROM
				buffer_ptr += base;

				// jump back to ROM
				fprintf( out_text, "\n" );
				fprintf( out_text, "\n<JMP.L>" );
				fprintf( out_text, "<$%02X><$%02X><$%02X><$%02X>",
					(buffer_ptr>>24)&0xff, (buffer_ptr>>16)&0xff,
					(buffer_ptr>>8)&0xff, (buffer_ptr>>0)&0xff );

				// adjust to ROM
				buffer_ptr = old_ptr;

				// space SAVINGS
				fprintf( out_text, "\n#FILL($%X, $%X, $00)",
					base+WRITE_START, base+buffer_ptr-1, base_name );
				fprintf( out_text, "\n" );


				// SAFETY CHECK
				if( WRITE_SIZE<3 )
				{
					fprintf( out_text, "\n//[WARN] INDEX WRITE_SIZE = %d", WRITE_SIZE );
				}				

				// ASM notes
				fprintf( out_text, "\n//" );

				if( EXIT==true ) break;
			}
		}

		// ------------------------------------------------------------------------
		// ------------------------------------------------------------------------

		// 8-bit font codes
		if( code>=0x20 && code<0x80 )
		{
			if( pass==0 && WRITE_ROM==1 ) WRITE_SIZE++;

			Print_Font( 0, code, code );
			continue;
		}

		if( code>=0xa0 && code<0xe0 )
		{
			if( pass==0 && WRITE_ROM==1 ) WRITE_SIZE++;

			Print_Font( 0, code, code );
			continue;
		}

		// ------------------------------------------------------------------------
		// ------------------------------------------------------------------------

		// 16-bit font codes (TRUE SJIS NUMBERING)
		if( code>=0x80 && code<0xa0 )
		{
			if( pass==0 && WRITE_ROM==1 ) WRITE_SIZE+=2;

			code <<= 8;
			code |= Read_Byte(1);

#ifdef NO_KANJI
			Print_Font( 0x100, code, code );
#else
			fputc( (code>>8)&0xff, out_text );
			fputc( (code>>0)&0xff, out_text );
#endif
			continue;
		}

		if( code>=0xe0 && code<0xeb )
		{
			if( pass==0 && WRITE_ROM==1 ) WRITE_SIZE+=2;

			code <<= 8;
			code |= Read_Byte(1);

#ifdef NO_KANJI
			Print_Font( 0x100, code, code );
#else
			fputc( (code>>8)&0xff, out_text );
			fputc( (code>>0)&0xff, out_text );
#endif
			continue;
		}

		// ------------------------------------------------------------------------
		// ------------------------------------------------------------------------

		// RAM dictionary code
		if( code==0x09 )
		{
			if( pass==0 && WRITE_ROM==1 ) WRITE_SIZE+=2;

			code <<= 8;
			code |= Read_Byte(1);

			Print_Code( 0x100, code, code );
			continue;
		}

		// ------------------------------------------------------------------------
		// ------------------------------------------------------------------------

		// CALL RET (inline)
		if( pass>0 )
		{
			// STOP
			if( code==0x00 ) break;
			if( code==0x06 ) break;
			if( code==0x07 ) break;
			if( code==0x0A ) break;
			if( code==0x0D ) break;
			if( code==0x17 ) break;
		}

		// inline CALLs
		if( code==0x10 )
		{
			int offset, old_ptr;

			// special case HACK - do NOT INLINE
			if( file_no==0xca && buffer_ptr==0x11a7+1 )
			{
				Print_Code( 0, code, code );
				Print_Byte(2);

				WRITE_ROM = 0;
				continue;
			}

			if( pass==0 && WRITE_ROM==1 ) WRITE_SIZE+=3;
			/*
			// SAFE - MULTIPLE INLINE NOT A PROBLEM
			if( pass>0 )
			{
				printf( "\n[DUMP_2] FAIL-SAFE $10 @ %04X", buffer_ptr-1 );
				break;
			}
			*/


			// Formatting
			offset = Peek_Word(1);

			fprintf( out_text, "\n" );
			fprintf( out_text, "\n//" );
			Print_Code( 0, code, code );
			fprintf( out_text, "<$%02X><$%02X>", (offset>>8)&0xff, (offset>>0)&0xff );
			fprintf( out_text, "\n" );


			// 16-bit relative (from opcode)
			offset = buffer_ptr;
			offset += (short) Read_Word(1);

			if( offset < start_offset )
			{
				offset += 0;
			}
			else if( offset < buffer_ptr )
			{
				printf( "\n[DUMP_2] FAIL-SAFE $10 PTR @ %04X", buffer_ptr-1 );
				break;
			}

			// run SUBROUTINE
			old_ptr = buffer_ptr;
			Dump_Layer3( offset, pass+1 );
			buffer_ptr = old_ptr;

			// inline DONE, auto-<LINE>
			if( last_code == 0x07 || last_code==0x0a || last_code==0x0d || last_code==0x17 )
				code = 0x01;
			else
				continue;
		}


		// FAIL-SAFE
		if( code==0x15 )
		{
			if( pass>0 )
			{
				// special case HACK - NOTATION ONLY
				if( file_no==0xca && buffer_ptr==0x12f4 )
				{
					// $12F4
					// <ASM 15><$00><$04>
					// <CODE 08>
					// <END 06>
				}
				else
				{
					printf( "\n[DUMP_2] FAIL-SAFE $15 @ %04X", buffer_ptr-1 );
					break;
				}
			}
		}

		// ------------------------------------------------------------------------
		// ------------------------------------------------------------------------

		// ASM code
		Print_Code( 0, code, code );
		if( pass==0 && WRITE_ROM==1 ) WRITE_SIZE++;

		// ------------------------------------------------------------------------
		// ------------------------------------------------------------------------

		// local dictionary table
		if( code==0x16 )
		{
			int offset[5+1], old_ptr;

			if( pass==0 && WRITE_ROM==1 ) WRITE_SIZE+=10;
			if( pass>0 )
			{
				printf( "\n[DUMP_2] FAIL-SAFE $16 @ %04X", buffer_ptr-1 );
				break;
			}

			// FIVE table entries
			for( int lcv=0; lcv<5; lcv++ )
			{
				// 16-bit relative
				offset[lcv] = buffer_ptr;
				offset[lcv] += (short) Read_Word(1);

				if( offset[lcv] < start_offset )
				{
					offset[lcv] += 0;
				}
				else if( offset[lcv] < buffer_ptr )
				{
					printf( "\n[DUMP_2] FAIL-SAFE $16 PTR @ %04X", buffer_ptr-1 );
					break;
				}

				fprintf( out_text, "\n#EMBSETREL(%d)", EMBED_COUNT+lcv );
			}

			// add JMP code
			fprintf( out_text, "\n" );
			Print_Code( 0, 0x0f, 0x0f );
			fprintf( out_text, "\n#EMBSETREL(%d)", EMBED_COUNT+lcv );
			fprintf( out_text, "\n" );


			// Formatting
			old_ptr = buffer_ptr;
			for( lcv=0; lcv<5; lcv++ )
			{
				fprintf( out_text, "\n#EMBWRITEREL(%d)", EMBED_COUNT+lcv );
				fprintf( out_text, "\n" );

				// run SUBROUTINE
				Dump_Layer3( offset[lcv], pass+1 );

				Print_Code( 0, last_code, last_code );
				fprintf( out_text, "\n" );
			}
			last_stop = buffer_ptr;
			buffer_ptr = old_ptr;


			// normal code
			fprintf( out_text, "\n#EMBWRITEREL(%d)", EMBED_COUNT+lcv );
			fprintf( out_text, "\n" );
			EMBED_COUNT += (5+1);
			continue;
		}

		// ------------------------------------------------------------------------
		// ------------------------------------------------------------------------

		// COND flags
		if( code==0x11 || code==0x12 )
		{
			jmp_cond = 1;
		}


		// JMP
		if( code==0x0F )
		{
			int offset;

			if( pass>0 )
			{
				printf( "\n[DUMP_2] FAIL-SAFE $0F @ %04X", buffer_ptr-1 );
				break;
			}

			offset = buffer_ptr;
			offset += (short) Peek_Word(1);
			Print_Byte(2);
			fprintf( out_text, "\n//" );

			if( offset < start_offset )
			{
				offset += 0;
			}
			else if( offset < buffer_ptr )
			{
				printf( "\n[DUMP_2] FAIL-SAFE $0F PTR @ %04X", buffer_ptr-1 );
				break;
			}

			// notate for future lookup
			ptr_list.push_back( base+offset );
			mark_rom[ base+offset ] |= TYPE_PASS2;

			// check code termination
			if( jmp_cond == 1 )
			{
				jmp_cond = 0;
				continue;
			}

			break;
		}

		// ------------------------------------------------------------------------
		// ------------------------------------------------------------------------

		// opcode ARGS
		if( code>=0xEB ) code -= 0xC0;
		Print_Byte( args_table[code] );

		if( pass==0 && WRITE_ROM==1 ) WRITE_SIZE += args_table[code];

		// ------------------------------------------------------------------------
		// ------------------------------------------------------------------------

		// STOP
		if( code==0x00 || code==0x06 )
		{
			fprintf( out_text, "\n//" );
			break;
		}

		// RET
		if( code==0x07 || code==0x0A || code==0x0D || code==0x17 )
		{
			fprintf( out_text, "\n//" );
			break;
		}

		// LINE / WAIT
		if( code==0x01 || code==0x03 )
		{
			if( WRITE_ROM==1 )
				fprintf( out_text, "\n" );
			else
				fprintf( out_text, "\n//" );
			continue;
		}

		// WAIT CLEAR
		if( code==0x05 )
		{
			if( WRITE_ROM==1 )
				fprintf( out_text, "\n\n" );
			else
				fprintf( out_text, "\n\n//" );
			continue;
		}
	} // end file

	// -------------------------------------------------------------------------
	// -------------------------------------------------------------------------

	if( pass==0 )
	{
		if( buffer_ptr>last_stop ) last_stop = buffer_ptr;


		// FILE information
		fprintf( out_text, "\n" );
		fprintf( out_text, "\n//[TEXT] %06X-%06X", file_ptr+base, last_stop+base );
		fprintf( out_text, "\n//////////////////////////////////////////////////////////" );
		fprintf( out_text, "\n" );
		fprintf( out_text, "\n" );

		printf( "\n[TEXT] %06X-%06X", file_ptr+base, last_stop+base );


		// code flow hacks - more text probably follows
		DUMP_HACKS;
		return;

dump_string:
		// notate for future lookup
		ptr_list.push_back( base+buffer_ptr );
		mark_rom[ base+buffer_ptr ] |= TYPE_PASS2;
	}
}


void Dump_Layer2a( int start_offset, int pass=0, int file_no=0 )
{
	int file_ptr, base;

	buffer_ptr = start_offset;
	base = 0;

	// dumper start
	if( pass==0 )
	{
		// no text checks
		SKIP_HACKS;

		// init
		file_ptr = start_offset;
		last_stop = start_offset;

		jmp_cond = 0;

		WRITE_ROM = 0;
		WRITE_SIZE = 0;

		//memset( mark_rom, 0, sizeof(mark_rom) );

		// -------------------------------------------------------------------------

		// safety check
		if( (mark_rom[ base+buffer_ptr ] & TYPE_DIRTY) )
		{
			return;
		}
		mark_rom[ base+buffer_ptr ] |= TYPE_DIRTY;

		if( LAST_DUMP > start_offset )
		{
			printf( "\n[DUMP] FAIL-SAFE REWIND @ %04X", start_offset );
		}
		LAST_DUMP = base + buffer_ptr;

		// Atlas header
		fprintf( out_text, "\n//[%06X]", base+start_offset );
		fprintf( out_text, "\n\n//" );
	}

	// -------------------------------------------------------------------------
	// -------------------------------------------------------------------------

	// dump string
	while(1)
	{
		int code;
		bool EXIT;

		// ptr state CHECK (don't duplicate data)
		EXIT = false;
		if( buffer_ptr > start_offset )
		{
			if( mark_rom[ base+buffer_ptr ] & TYPE_PASS2 )
			{
				EXIT = true;
				goto turn_off_ROM;
			}
		}

		// ------------------------------------------------------------------------
		// ------------------------------------------------------------------------

		// Read script
		code = Read_Byte(1);
		last_code = code;

		// ------------------------------------------------------------------------
		// ------------------------------------------------------------------------

		if( pass==0 )
		{
			// opcodes to turn ON ROM WRITING
			if(
				code==0x02 ||
				code==0x0B ||	code==0x0E ||
				code==0x10 || code==0x16 ||
				(code>=0x20 && code<=0xeb) )
			{
				// special case HACK - do NOT INLINE CALLs
				if( file_no==0xca && buffer_ptr==0x11a7+1 )
				{
					if(WRITE_ROM) goto turn_off_ROM;
					else WRITE_ROM = 0;
				}

				// turn ON check
				else if( WRITE_ROM==0 )
				{
					WRITE_ROM = 1;
					WRITE_SIZE = 0;
					WRITE_START = buffer_ptr+2;

					// mark ROM
					fprintf( out_text, "\n" );
					fprintf( out_text, "\n#WRITE(PtrTable)" );
					fprintf( out_text, "\n#W08BYTE($%X, $EB, \"insert/%s\")", buffer_ptr-1, base_name );
					fprintf( out_text, "\n#WRITEINDEX($%X, 2, \"insert/%s\")", buffer_ptr+0, base_name );
					fprintf( out_text, "\n" );
					fprintf( out_text, "\n" );
				}

				// ALREADY ON
			}


			// IGNORE opcodes
			else if(
				code==0x01 || code==0x03 || code==0x04 || code==0x05 || code==0x08 || code==0x09 ||
				code==0x0C ||	code==0x13 ||	code==0x14 ||
				code==0x18 ||	code==0x19 ||	code==0x1A ||
				code==0x1B || code==0x1C || code==0x1D ||	code==0x1E ||	code==0x1F )
			{}


			// remaining opcodes to turn OFF ROM WRITING
			else if( WRITE_ROM==1 )
			{
				int old_ptr;

turn_off_ROM:
				if( WRITE_ROM==0 ) break;

				WRITE_ROM = 0;
				//WRITE_SIZE--;
				old_ptr = buffer_ptr;


				// special case - index WARN hacks (3-byte space issue)
				if(0) {}
				else if( file_no==0x15 && buffer_ptr==0x1715+1 )
				{
					// Rewire JMP code (use DIRECT JMP.L)
					buffer_ptr = 0x171c;

					WRITE_SIZE = 3;
				}
				else if( file_no==0x15 && buffer_ptr==0x1769+1 )
				{
					// Rewire JMP code (use DIRECT JMP.L)
					buffer_ptr = 0x1770;

					WRITE_SIZE = 3;
				}
				else if( file_no==0x15 && buffer_ptr==0x17cd+1 )
				{
					// Rewire JMP code (use DIRECT JMP.L)
					buffer_ptr = 0x17d4;

					WRITE_SIZE = 3;
				}
				else if( EXIT==0 )
					buffer_ptr--;


				// adjust to RAM
				buffer_ptr += 0x6650;

				// jump back to ROM
				fprintf( out_text, "\n" );
				fprintf( out_text, "\n<JMP.L>" );
				fprintf( out_text, "<$FF><$FF><$%02X><$%02X>",
					(buffer_ptr>>8)&0xff, (buffer_ptr>>0)&0xff );

				// adjust to ROM
				buffer_ptr = old_ptr;

				// space SAVINGS
				fprintf( out_text, "\n#FILL($%X, $%X, $00, \"insert//%s\")",
					WRITE_START, buffer_ptr-1, base_name );
				fprintf( out_text, "\n" );


				// SAFETY CHECK
				if( WRITE_SIZE<3 )
				{
					fprintf( out_text, "\n//[WARN] INDEX WRITE_SIZE = %d", WRITE_SIZE );
				}				

				// ASM notes
				fprintf( out_text, "\n//" );

				if( EXIT==true ) break;
			}
		}

		// ------------------------------------------------------------------------
		// ------------------------------------------------------------------------

		// 8-bit font codes
		if( code>=0x20 && code<0x80 )
		{
			if( pass==0 && WRITE_ROM==1 ) WRITE_SIZE++;

			Print_Font( 0, code, code );
			continue;
		}

		if( code>=0xa0 && code<0xe0 )
		{
			if( pass==0 && WRITE_ROM==1 ) WRITE_SIZE++;

			Print_Font( 0, code, code );
			continue;
		}

		// ------------------------------------------------------------------------
		// ------------------------------------------------------------------------

		// 16-bit font codes (TRUE SJIS NUMBERING)
		if( code>=0x80 && code<0xa0 )
		{
			if( pass==0 && WRITE_ROM==1 ) WRITE_SIZE+=2;

			code <<= 8;
			code |= Read_Byte(1);

#ifdef NO_KANJI
			Print_Font( 0x100, code, code );
#else
			fputc( (code>>8)&0xff, out_text );
			fputc( (code>>0)&0xff, out_text );
#endif
			continue;
		}

		if( code>=0xe0 && code<0xeb )
		{
			if( pass==0 && WRITE_ROM==1 ) WRITE_SIZE+=2;

			code <<= 8;
			code |= Read_Byte(1);

#ifdef NO_KANJI
			Print_Font( 0x100, code, code );
#else
			fputc( (code>>8)&0xff, out_text );
			fputc( (code>>0)&0xff, out_text );
#endif
			continue;
		}

		// ------------------------------------------------------------------------
		// ------------------------------------------------------------------------

		// RAM dictionary code
		if( code==0x09 )
		{
			if( pass==0 && WRITE_ROM==1 ) WRITE_SIZE+=2;

			code <<= 8;
			code |= Read_Byte(1);

			Print_Code( 0x100, code, code );
			continue;
		}

		// ------------------------------------------------------------------------
		// ------------------------------------------------------------------------

		// CALL RET (inline)
		if( pass>0 )
		{
			// STOP
			if( code==0x00 ) break;
			if( code==0x06 ) break;
			if( code==0x07 ) break;
			if( code==0x0A ) break;
			if( code==0x0D ) break;
		}

		// inline CALLs
		if( code==0x10 )
		{
			int offset, old_ptr;

			// special case HACK - do NOT INLINE
			if( file_no==0xca && buffer_ptr==0x11a7+1 )
			{
				Print_Code( 0, code, code );
				Print_Byte(2);

				WRITE_ROM = 0;
				continue;
			}

			if( pass==0 && WRITE_ROM==1 ) WRITE_SIZE+=3;
			/*
			// SAFE - MULTIPLE INLINE NOT A PROBLEM
			if( pass>0 )
			{
				printf( "\n[DUMP_2] FAIL-SAFE $10 @ %04X", buffer_ptr-1 );
				break;
			}
			*/


			// Formatting
			offset = Peek_Word(1);

			fprintf( out_text, "\n" );
			fprintf( out_text, "\n//" );
			Print_Code( 0, code, code );
			fprintf( out_text, "<$%02X><$%02X>", (offset>>8)&0xff, (offset>>0)&0xff );
			fprintf( out_text, "\n" );


			// 16-bit relative (from opcode)
			offset = buffer_ptr;
			offset += (short) Read_Word(1);

			if( offset < start_offset )
			{
				offset += 0;
			}
			else if( offset < buffer_ptr )
			{
				printf( "\n[DUMP_2] FAIL-SAFE $10 PTR @ %04X", buffer_ptr-1 );
				break;
			}

			// run SUBROUTINE
			old_ptr = buffer_ptr;
			Dump_Layer2a( offset, pass+1 );
			buffer_ptr = old_ptr;

			// inline DONE, auto-<LINE>
			if( last_code == 0x07 || last_code==0x0a || last_code==0x0d || last_code==0x17 )
				code = 0x01;
			else
				continue;
		}


		// FAIL-SAFE
		if( code==0x15 )
		{
			if( pass>0 )
			{
				// special case HACK - NOTATION ONLY
				if( file_no==0xca && buffer_ptr==0x12f4 )
				{
					// $12F4
					// <ASM 15><$00><$04>
					// <CODE 08>
					// <END 06>
				}
				else
				{
					printf( "\n[DUMP_2] FAIL-SAFE $15 @ %04X", buffer_ptr-1 );
					break;
				}
			}
		}

		// ------------------------------------------------------------------------
		// ------------------------------------------------------------------------

		// ASM code
		Print_Code( 0, code, code );
		if( pass==0 && WRITE_ROM==1 ) WRITE_SIZE++;

		// ------------------------------------------------------------------------
		// ------------------------------------------------------------------------

		// local dictionary table
		if( code==0x16 )
		{
			int offset[5+1], old_ptr;

			if( pass==0 && WRITE_ROM==1 ) WRITE_SIZE+=10;
			if( pass>0 )
			{
				printf( "\n[DUMP_2] FAIL-SAFE $16 @ %04X", buffer_ptr-1 );
				break;
			}

			// FIVE table entries
			for( int lcv=0; lcv<5; lcv++ )
			{
				// 16-bit relative
				offset[lcv] = buffer_ptr;
				offset[lcv] += (short) Read_Word(1);

				if( offset[lcv] < start_offset )
				{
					offset[lcv] += 0;
				}
				else if( offset[lcv] < buffer_ptr )
				{
					printf( "\n[DUMP_2] FAIL-SAFE $16 PTR @ %04X", buffer_ptr-1 );
					break;
				}

				fprintf( out_text, "\n#EMBSETREL(%d)", EMBED_COUNT+lcv );
			}

			// add JMP code
			fprintf( out_text, "\n" );
			Print_Code( 0, 0x0f, 0x0f );
			fprintf( out_text, "\n#EMBSETREL(%d)", EMBED_COUNT+lcv );
			fprintf( out_text, "\n" );


			// Formatting
			old_ptr = buffer_ptr;
			for( lcv=0; lcv<5; lcv++ )
			{
				fprintf( out_text, "\n#EMBWRITEREL(%d)", EMBED_COUNT+lcv );
				fprintf( out_text, "\n" );

				// run SUBROUTINE
				Dump_Layer2a( offset[lcv], pass+1 );

				Print_Code( 0, last_code, last_code );
				fprintf( out_text, "\n" );
			}
			last_stop = buffer_ptr;
			buffer_ptr = old_ptr;


			// normal code
			fprintf( out_text, "\n#EMBWRITEREL(%d)", EMBED_COUNT+lcv );
			fprintf( out_text, "\n" );
			EMBED_COUNT += (5+1);
			continue;
		}

		// ------------------------------------------------------------------------
		// ------------------------------------------------------------------------

		// COND flags
		if( code==0x11 || code==0x12 )
		{
			jmp_cond = 1;
		}


		// JMP
		if( code==0x0F )
		{
			int offset;

			if( pass>0 )
			{
				printf( "\n[DUMP_2] FAIL-SAFE $0F @ %04X", buffer_ptr-1 );
				break;
			}

			offset = buffer_ptr;
			offset += (short) Peek_Word(1);
			Print_Byte(2);
			fprintf( out_text, "\n//" );

			if( offset < start_offset )
			{
				offset += 0;
			}
			else if( offset < buffer_ptr )
			{
				printf( "\n[DUMP_2] FAIL-SAFE $0F PTR @ %04X", buffer_ptr-1 );
				break;
			}

			// notate for future lookup
			ptr_list.push_back( base+offset );
			mark_rom[ base+offset ] |= TYPE_PASS2;

			// check code termination
			if( jmp_cond == 1 )
			{
				jmp_cond = 0;
				continue;
			}

			break;
		}

		// ------------------------------------------------------------------------
		// ------------------------------------------------------------------------

		// opcode ARGS
		if( code>=0xEB ) code -= 0xC0;
		Print_Byte( args_table[code] );

		if( pass==0 && WRITE_ROM==1 ) WRITE_SIZE += args_table[code];

		// ------------------------------------------------------------------------
		// ------------------------------------------------------------------------

		// STOP
		if( code==0x00 || code==0x06 )
		{
			fprintf( out_text, "\n//" );
			break;
		}

		// RET
		if( code==0x07 || code==0x0A || code==0x0D || code==0x17 )
		{
			fprintf( out_text, "\n//" );
			break;
		}

		// LINE / WAIT
		if( code==0x01 || code==0x03 )
		{
			if( WRITE_ROM==1 )
				fprintf( out_text, "\n" );
			else
				fprintf( out_text, "\n//" );
			continue;
		}

		// WAIT CLEAR
		if( code==0x05 )
		{
			if( WRITE_ROM==1 )
				fprintf( out_text, "\n\n" );
			else
				fprintf( out_text, "\n\n//" );
			continue;
		}
	} // end file

	// -------------------------------------------------------------------------
	// -------------------------------------------------------------------------

	if( pass==0 )
	{
		if( buffer_ptr>last_stop ) last_stop = buffer_ptr;

		
		// FILE information
		fprintf( out_text, "\n" );
		fprintf( out_text, "\n//[TEXT] %06X-%06X [%06X-%06X]", file_ptr+base, last_stop+base,
			0x6650+file_ptr, 0x6650+last_stop );
		fprintf( out_text, "\n//////////////////////////////////////////////////////////" );
		fprintf( out_text, "\n" );
		fprintf( out_text, "\n" );

		printf( "\n[TEXT] %06X-%06X", file_ptr+base, last_stop+base );


		// code flow hacks - more text probably follows
		DUMP_HACKS;
		return;

dump_string:
		// notate for future lookup
		ptr_list.push_back( base+buffer_ptr );
		mark_rom[ base+buffer_ptr ] |= TYPE_PASS2;
	}
}


void Dump_Layer2( int start_offset, int pass=0, int file_no=0 )
{
	int file_ptr, base;

	buffer_ptr = start_offset;
	base = 0;

	// dumper start
	if( pass==0 )
	{
		// no text checks
		SKIP_HACKS;

		// init
		file_ptr = start_offset;

		last_stop = start_offset;
		jmp_cond = 0;

		//memset( mark_rom, 0, sizeof(mark_rom) );

		// -------------------------------------------------------------------------

		// safety check
		if( (mark_rom[ base+buffer_ptr ] & TYPE_PASS3) )
		{
			return;
		}
		mark_rom[ base+buffer_ptr ] |= TYPE_PASS3;
	}

	// -------------------------------------------------------------------------
	// -------------------------------------------------------------------------

	// scan string (no dump)
	while(1)
	{
		int code;

		// ptr state CHECK (don't duplicate data)
		if( buffer_ptr > start_offset )
		{
			if( mark_rom[ base+buffer_ptr ] & TYPE_PASS2 ) break;
		}

		// ------------------------------------------------------------------------

		code = Read_Byte(1);
		last_code = code;

		// ------------------------------------------------------------------------

		// 8-bit font codes
		if( code>=0x20 && code<0x80 )
		{
			continue;
		}

		if( code>=0xa0 && code<0xe0 )
		{
			continue;
		}

		// ------------------------------------------------------------------------

		// 16-bit font codes (TRUE SJIS NUMBERING)
		if( code>=0x80 && code<0xa0 )
		{
			code <<= 8;
			code |= Read_Byte(1);

			continue;
		}

		if( code>=0xe0 && code<0xeb )
		{
			code <<= 8;
			code |= Read_Byte(1);

			continue;
		}

		// ------------------------------------------------------------------------
		// ------------------------------------------------------------------------

		// RAM dictionary code
		if( code==0x09 )
		{
			code <<= 8;
			code |= Read_Byte(1);

			continue;
		}

		// ------------------------------------------------------------------------
		// ------------------------------------------------------------------------

		// CALL (inline)
		if( code==0x10 )
		{
			int offset;

			/*
			// SAFE - MULTIPLE INLINE NOT A PROBLEM
			if( pass>0 )
			{
				printf( "\n[DUMP_2] FAIL-SAFE $10 @ %04X", buffer_ptr-1 );
				break;
			}
			*/

			// 16-bit relative (from opcode)
			offset = buffer_ptr;
			offset += (short) Read_Word(1);

			if( offset < start_offset )
			{
				offset += 0;
			}
			else if( offset < buffer_ptr )
			{
				printf( "\n[DUMP_2] FAIL-SAFE @ %04X", buffer_ptr-1 );
				break;
			}

			continue;
		}


		// FAIL-SAFE
		if( code==0x15 || code==0x16 )
		{
			if( pass>0 )
			{
				printf( "\n[DUMP_2] FAIL-SAFE @ %04X", buffer_ptr-1 );
				break;
			}
		}

		// ------------------------------------------------------------------------
		// ------------------------------------------------------------------------

		// ASM code
		//Print_Code( 0, code, code );

		// ------------------------------------------------------------------------
		// ------------------------------------------------------------------------

		// local dictionary table
		if( code==0x16 )
		{
			int offset[5+1], old_ptr;

			if( pass>0 )
			{
				printf( "\n[DUMP_2] FAIL-SAFE @ %04X", buffer_ptr-1 );
				break;
			}

			// FIVE table entries
			for( int lcv=0; lcv<5; lcv++ )
			{
				// 16-bit relative
				offset[lcv] = buffer_ptr;
				offset[lcv] += (short) Read_Word(1);

				if( offset[lcv] < start_offset )
				{
					offset[lcv] += 0;
				}
				else if( offset[lcv] < buffer_ptr )
				{
					printf( "\n[DUMP_2] FAIL-SAFE @ %04X", buffer_ptr-1 );
					break;
				}
			}

			
			// Formatting
			old_ptr = buffer_ptr;
			for( lcv=0; lcv<5; lcv++ )
			{
				// run SUBROUTINE
				Dump_Layer2( offset[lcv], pass+1, file_no );
			}
			last_stop = buffer_ptr;
			buffer_ptr = old_ptr;

			continue;
		}

		// ------------------------------------------------------------------------
		// ------------------------------------------------------------------------

		// COND flags
		if( code==0x11 || code==0x12 )
		{
			jmp_cond = 1;
		}


		// JMP
		if( code==0x0F )
		{
			int offset;

			if( pass>0 )
			{
				printf( "\n[DUMP_2] FAIL-SAFE @ %04X", buffer_ptr-1 );
				break;
			}

			offset = buffer_ptr;
			offset += (short) Read_Word(1);

			if( offset < start_offset )
			{
				offset += 0;
			}
			else if( offset < buffer_ptr )
			{
				printf( "\n[DUMP_2] FAIL-SAFE @ %04X", buffer_ptr-1 );
				break;
			}

			// notate for future lookup
			ptr_list.push_back( base+offset );
			mark_rom[ base+offset ] |= TYPE_PASS2;

			// check code termination
			if( jmp_cond == 1 )
			{
				jmp_cond = 0;
				continue;
			}

			break;
		}

		// ------------------------------------------------------------------------
		// ------------------------------------------------------------------------

		// opcode ARGS
		if( code>=0xEB ) code -= 0xCB;
		Read_Byte( args_table[code] );

		// ------------------------------------------------------------------------
		// ------------------------------------------------------------------------

		// STOP
		if( code==0x00 || code==0x06 )
		{
			break;
		}

		// RET
		if( code==0x07 || code==0x0A || code==0x0D )
		{
			break;
		}

		// LINE / WAIT / WAIT CLEAR
		if( code==0x01 || code==0x03 || code==0x05 )
		{
			continue;
		}
	} // end file

	// -------------------------------------------------------------------------
	// -------------------------------------------------------------------------

	if( pass==0 )
	{
		last_stop = buffer_ptr;

		fprintf( out_text, "\n//[TEXT] %06X-%06X [%06X-%06X]", file_ptr+base, last_stop+base,
			0x6650+file_ptr, 0x6650+last_stop );


		// CHECK ptr replacement problems
		if( last_stop-file_ptr < 3+0 )
		//if( last_stop-file_ptr < 3+3 )
		{
			fprintf( out_text, "\n[WARN] SPACE!" );
		}


		// code flow hacks - more text probably follows
		DUMP_HACKS;
		return;

dump_string:
		// notate for future lookup
		ptr_list.push_back( base+buffer_ptr );
		mark_rom[ base+buffer_ptr ] |= TYPE_PASS2;
	}
}


void Dump_Layer1()
{
	int lcv;

	// init
	ptr_list.clear();
	memset( mark_rom, 0, sizeof(mark_rom) );

	for( lcv=0; lcv<BUFFER_SIZE; )
	{
		bool found;
		int ptr;
		short offset;

		// -----------------------------------------------------------

		// Dragon Slayer II
		//0x2A, 0x7C, -1, -1, -1, -1,		// MOVE.l #$xxxxxxxx,A5

		const int string_str[] = {
			0x43, 0xFA, -1, -1,						// LEA $xxxx(PC),A1
			0x3A, 0x7C, -1, -1,						// MOVE.w #$xxxx,A5
			0x2C, 0x78,	0x02, 0x00,				// MOVE.l ($0200),A6
			0x4E, 0x96										// JSR (A6)
		};
		found = true;

		// Look for hard-coded strings
		for( ptr=0; ptr<14; ptr++ )
		{
			if( lcv+ptr >= BUFFER_SIZE ) break;

			if( string_str[ptr] == -1 ) continue;
			if( string_str[ptr] != buffer[lcv+ptr] )
			{
				found = false;
				break;
			}
		}
		if(!found) goto scan_2;

		// string ptr found (MSB-16)
		offset = (buffer[lcv+2])<<8;
		offset |= (buffer[lcv+3])<<0;
		ptr = offset + (lcv+2);

		// mark information
		ptr_list.push_back(ptr);
		mark_rom[ ptr ] |= TYPE_PASS2;

		//printf( "\n%X", ptr );
		fprintf( stderr, "\n%X", ptr );

		lcv += 14;
		continue;

		// -----------------------------------------------------------

scan_2:
		lcv++;
		continue;
	}
}
