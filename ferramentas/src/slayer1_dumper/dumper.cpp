#include <stdio.h>
#include <string.h>
#include <deque>

using std::deque;

// -------------------------------------------------------------------------

int buffer_ptr;

char line[512];
char base_name[512];

int last_ptr;

FILE *out_text, *out_binary;
FILE *rom;

#define MSB
#include "table.cpp"
#include "scan.cpp"
#include "decode.cpp"
#include "encode.cpp"

// -------------------------------------------------------------------------

int main( int argc, char** argv )
{
	if( argc<2 ) { fprintf( stderr, "ERROR - no ROM args\n" ); return -1; }

	rom = fopen( argv[2], "rb" );
	if( !rom ) { fprintf( stderr, "ERROR - no ROM file\n" ); return -1; }

	// ----------------------------------------------------------------
	// ****************************************************************
	// ----------------------------------------------------------------

	if( strcmp(argv[1],"DUMP_FILE") == 0 )
	{
		char out_name[512];

		Load_Table( 0x00, "table//table_main_8x14.txt" );

		// -------------------------------------------------------------------
		// -------------------------------------------------------------------

		/*
		out_text = fopen( "temp.txt", "w" );
		if( !out_text ) { fprintf( stderr, "ERROR - no TEXT dir\n" ); return -1; }
		{
			for( int scene=0; scene<225; scene++ )
			{
				fprintf( out_text, "\natlas \"Dragon Slayer (J) [!].bin\" \"text//script_%02X.txt\" > \"logs//log_atlas_%02X.txt\"",
					scene, scene);
			}
		}
		fclose(out_text);
		*/

		for( int scene=0; scene<225; scene++ )
		//for( int scene=0x2c; scene<225; scene++ )
		{
			int ptr;

			sprintf( out_name, "text//script_%02X.txt", scene );
			out_text = fopen( out_name, "w" );
			if( !out_text ) { fprintf( stderr, "ERROR - no TEXT dir\n" ); return -1; }

			// Atlas header
			fprintf( out_text, "#VAR(Table, TABLE)\n" );
			fprintf( out_text, "#ADDTBL(\"slayer1_table.txt\", Table)\n" );
			fprintf( out_text, "#ACTIVETBL(Table)\n" );
			fprintf( out_text, "\n" );
			fprintf( out_text, "#SMA(\"LINEAR\")\n" );
			fprintf( out_text, "#EMBTYPE(\"MSB16\", 16, $2)\n" );
			fprintf( out_text, "\n" );
			fprintf( out_text, "#VAR(MyPtr, CUSTOMPOINTER)\n" );
			fprintf( out_text, "#VAR(PtrTable, POINTERTABLE)\n" );
			fprintf( out_text, "\n" );
			fprintf( out_text, "#CREATEPTR(MyPtr, \"MSB32\", $0, 32)\n" );
			fprintf( out_text, "#PTRTBL(PtrTable, $200000, 4, MyPtr)\n" );
			fprintf( out_text, "\n" );
			fprintf( out_text, "//---------------------------------------------------------\n" );
			fprintf( out_text, "//---------------------------------------------------------\n" );
			fprintf( out_text, "\n" );
			fprintf( out_text, "#LOADPC( \"text//atlas_pc.txt\" )\n" );
			fprintf( out_text, "#LOADINDEX( \"text//atlas_index.txt\" )\n" );
			fprintf( out_text, "#LOADPTRTABLE( PtrTable, \"text//atlas_ptrtable.txt\" )\n" );
			fprintf( out_text, "\n" );

			// ----------------------------------------------------------
			// ----------------------------------------------------------

			// open main file
			rom = fopen( argv[2], "rb" );
			Cache_Buffer( 0x134fa0 );
	
			ptr = Read_Dword(scene+1);
			ptr += 0x134fa0;

			sprintf( base_name, "%02X_%X.bin", scene, ptr );
			sprintf( out_name, "binary//%02X_%X.bin", scene, ptr );
			out_binary = fopen( out_name, "wb" );

			// ----------------------------------------------------------
			// ----------------------------------------------------------

			// bypass header
			fprintf( stderr, "\n[DECODE] %s", out_name );
			Decode_Start(ptr+2);

			// ---------------------------------------------------------------
			// ---------------------------------------------------------------

			// switch modes
			if(out_binary) fclose(out_binary);
			if(rom) fclose(rom);
			
			fprintf( stderr, "\n[DUMP] %s", out_name );
			printf( "\n[DUMP] %s", out_name );

			rom = fopen( out_name, "rb" );
			Cache_Buffer(0);

			// scan file for list of hard pointers
			Dump_Layer1();
			EMBED_COUNT = 0;
			LAST_DUMP = -1;

			// Atlas header
			fprintf( out_text, "\n//////////////////////////////////////////////////////////" );
			fprintf( out_text, "\n//********************************************************" );
			fprintf( out_text, "\n//[FILE] %s", out_name );
			fprintf( out_text, "\n\n" );

			// BAD FILE..(BAD TEXT PTRS)..?!
			if( scene==0xa1 )
			{
				ptr_list.erase( ptr_list.begin(), ptr_list.end() );
			}

			// now dump list of text
			for( int lcv=0; lcv<ptr_list.size(); lcv++ )
			{
				int min, index;

				min = 0x10000;
				index = 0;
				for( int lcv2=0; lcv2<ptr_list.size(); lcv2++ )
				{
					// sorted order
					if( ptr_list[lcv2]<min )
					{
						min = ptr_list[lcv2];
						index = lcv2;
					}
				}

				Dump_Layer2a( ptr_list[index], 0, scene );
				ptr_list[index] = 0x10000;
			}


			// Atlas post-header
			fprintf( out_text, "\n" );
			fprintf( out_text, "#SAVEPC( \"text//atlas_pc.txt\" )\n" );
			fprintf( out_text, "#SAVEINDEX( \"text//atlas_index.txt\" )\n" );
			fprintf( out_text, "#SAVEPTRTABLE( PtrTable, \"text//atlas_ptrtable.txt\" )\n" );

			if(out_binary) fclose(out_binary);
			if(rom) fclose(rom);

			// ---------------------------------------------------------------
			// ---------------------------------------------------------------

			// ENCODE test
			//rom = fopen( out_name, "rb" );
			//out_binary = fopen("binary/test.bin","wb");

			//Cache_Buffer(0);
			//LZ_Encode(rom,out_binary);
		}
	}

	// ----------------------------------------------------------------
	// ****************************************************************
	// ----------------------------------------------------------------

	if( strcmp(argv[1],"INSERT_FILE") == 0 )
	{
		char out_name[512];
		int start, stop;

		// open ROM
		out_binary = fopen( argv[2], "rb+" );
		sscanf( argv[3], "%X", &start );
		sscanf( argv[4], "%X", &stop );

		// -------------------------------------------------------------------
		// -------------------------------------------------------------------

		for( int scene=start; scene<=stop; scene++ )
		{
			int ptr, file_end;

			// read FILE offset
			Cache_Buffer( 0x134fa0, out_binary );
			ptr = Read_Dword(scene+1);

			// check FILE end
			file_end = Peek_Dword(1) + 0x134fa0;
			if( scene==224 ) file_end = 0x1918D2;

			// open main file (skip 2-byte header)
			ptr += 0x134fa0;
			fseek( out_binary, ptr+2, SEEK_SET );

			// open sub-file
			sprintf( base_name, "%02X_%X.bin", scene, ptr );
			sprintf( out_name, "insert//%02X_%X.bin", scene, ptr );
			rom = fopen( out_name, "rb" );

			// ---------------------------------------------------------------
			// ---------------------------------------------------------------

			fprintf( stderr, "\n[FILE %02X]", scene );

			// ENCODE test
			LZ_Encode(rom,out_binary);

			// Information
			printf( "\n[FILE %02X] %X-%X  [%X]",
				scene, ptr+2, ftell(out_binary), file_end );
			if( ftell(out_binary) > file_end )
			{
				printf( "\nOVERWRITE = %X bytes", ftell(out_binary)-file_end );
			}

			if(rom) fclose(rom);
		}

		if(out_binary) fclose(out_binary);
	}

	// ----------------------------------------------------------------
	// ****************************************************************
	// ----------------------------------------------------------------

	if( strcmp(argv[1],"DUMP_STRINGS") == 0 )
	{
		char out_name[512];
		FILE *dump_log;

		Load_Table( 0x00, "table//table_main_8x14.txt" );

		sprintf( out_name, "text//strings.txt" );
		out_text = fopen( out_name, "w" );
		if( !out_text ) { fprintf( stderr, "ERROR - no TEXT dir\n" ); return -1; }

		dump_log = fopen( "text//dump_strings.txt", "r" );
		if( !dump_log ) { fprintf( stderr, "ERROR - no STRINGS file\n" ); return -1; }

		// Atlas header
		fprintf( out_text, "#VAR(Table, TABLE)\n" );
		fprintf( out_text, "#ADDTBL(\"slayer1_table.txt\", Table)\n" );
		fprintf( out_text, "#ACTIVETBL(Table)\n" );
		fprintf( out_text, "\n" );
		fprintf( out_text, "#SMA(\"LINEAR\")\n" );
		fprintf( out_text, "#EMBTYPE(\"MSB16\", 16, $2)\n" );
		fprintf( out_text, "\n" );
		fprintf( out_text, "#VAR(MyPtr, CUSTOMPOINTER)\n" );
		fprintf( out_text, "#VAR(PtrTable, POINTERTABLE)\n" );
		fprintf( out_text, "\n" );
		fprintf( out_text, "#CREATEPTR(MyPtr, \"MSB32\", $0, 32)\n" );
		fprintf( out_text, "#PTRTBL(PtrTable, $200000, 4, MyPtr)\n" );
		fprintf( out_text, "\n" );
		fprintf( out_text, "//---------------------------------------------------------\n" );
		fprintf( out_text, "//---------------------------------------------------------\n" );
		fprintf( out_text, "\n" );
		fprintf( out_text, "#LOADPC( \"text//atlas_pc.txt\" )\n" );
		fprintf( out_text, "#LOADINDEX( \"text//atlas_index.txt\" )\n" );
		fprintf( out_text, "#LOADPTRTABLE( PtrTable, \"text//atlas_ptrtable.txt\" )\n" );
		fprintf( out_text, "\n" );

		// -------------------------------------------------------------------
		// -------------------------------------------------------------------

		// open main file
		rom = fopen( argv[2], "rb" );
		ptr_list.erase( ptr_list.begin(), ptr_list.end() );

		while(1)
		{
			int ptr;
			char line[64];

			// read line
			fgets( line, 64, dump_log );
			if( feof(dump_log) ) break;
			if(line[0]==';') continue;
			if(line[0]==0x0d) continue;
			if(line[0]==0x0a) continue;
			if(line[0]==' ') continue;

			// open main file
			sscanf( line, "%X", &ptr );

			// init
			ptr_list.push_back( ptr );
			mark_rom[ ptr ] |= TYPE_PASS2;
		}
	
		// ----------------------------------------------------------
		// ----------------------------------------------------------

		// now dump list of text
		for( int lcv=0; lcv<ptr_list.size(); lcv++ )
		{
			int min, index;

			min = 0x40 * 0x10000;
			index = 0;
			for( int lcv2=0; lcv2<ptr_list.size(); lcv2++ )
			{
				// sorted order
				if( ptr_list[lcv2]<min )
				{
					min = ptr_list[lcv2];
					index = lcv2;
				}
			}

			Dump_Layer3( ptr_list[index], 0, -1 );
			ptr_list[index] = 0x40 * 0x10000;

			fprintf( out_text, "\n#EMBCLEAR()" );
			fprintf( out_text, "\n" );
		}


		// Atlas post-header
		fprintf( out_text, "\n" );
		fprintf( out_text, "#SAVEPC( \"text//atlas_pc.txt\" )\n" );
		fprintf( out_text, "#SAVEINDEX( \"text//atlas_index.txt\" )\n" );
		fprintf( out_text, "#SAVEPTRTABLE( PtrTable, \"text//atlas_ptrtable.txt\" )\n" );

		// ---------------------------------------------------------------
		// ---------------------------------------------------------------

		// ENCODE test
		//rom = fopen( out_name, "rb" );
		//out_binary = fopen("binary/test.bin","wb");

		//Cache_Buffer(0);
		//LZ_Encode(rom,out_binary);

		if(dump_log) fclose(dump_log);
	}

	// ----------------------------------------------------------------
	// ****************************************************************
	// ----------------------------------------------------------------

	if(rom) fclose(rom);
	if(out_text) fclose(out_text);

	return 0;
}
