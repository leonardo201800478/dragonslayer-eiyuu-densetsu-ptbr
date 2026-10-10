unsigned char out_buffer[0x10000];
int buf_ptr;

int barrel, barrel_count;


int Shift_Barrel()
{
	int bit;

	if( barrel_count==0 )
	{
		barrel = Read_Byte(1);
		barrel |= (Read_Byte(1)<<8);
		barrel_count = 16;
	}

	bit = barrel&1;

	barrel >>= 1;
	barrel_count--;

	return bit;
}


void Decode_Hybrid()
{
	bool stop;

	barrel_count = 0;
	buf_ptr = 0;
	stop = false;

	while(1)
	{
		// force load barrel
		barrel = Read_Word(1);
		barrel_count = 8;

		while(1)
		{
			int lz_window, lz_run;

			// init
			lz_window = 0;
			lz_run = 0;

			// debug
			//if(buffer_ptr>=0x5000)
				//lz_run=0;

			if( Shift_Barrel()==0 )
			{
				// Raw
				out_buffer[ buf_ptr++ ] = Read_Byte(1);
				fputc( out_buffer[buf_ptr-1], out_binary );
				continue;
			}

			if( Shift_Barrel()==0 )
			{
				// 8-bit window
				lz_window = Read_Byte(1);
			}
			else
			{
				// 12-bit window
				for( int lcv=12; lcv>=8; lcv-- )
				{
					lz_window <<= 1;
					lz_window |= Shift_Barrel();
				}
				lz_window <<= 8;
				lz_window |= Read_Byte(1);

				// fail-safe: check STOP
				if( lz_window==0 ) break;

				// RLE
				if( lz_window==1 )
				{
					int flag, RLE_byte;

					flag = Shift_Barrel();

					// 4-bit run
					for( int lcv=3; lcv>=0; lcv-- )
					{
						lz_run <<= 1;
						lz_run |= Shift_Barrel();
					}

					// 12-bit run
					if( flag==1 )
					{
						lz_run <<= 8;
						lz_run |= Read_Byte(1);
					}

					RLE_byte = Read_Byte(1);
					lz_run += 0xd;

					// DBFa
					lz_run++;

					// RLE copy
					while( lz_run-- )
					{
						out_buffer[ buf_ptr++ ] = RLE_byte;
						fputc( RLE_byte, out_binary );
					}

					continue;
				} // end RLE
			} // end LZ window

			// LZ run
			if(0) {}
			else if( Shift_Barrel()==1 )
				lz_run=1;
			else if( Shift_Barrel()==1 )
				lz_run=2;
			else if( Shift_Barrel()==1 )
				lz_run=3;
			else if( Shift_Barrel()==1 )
				lz_run=4;
			else if( Shift_Barrel()==0 )
				lz_run = Read_Byte(1) + 0xd;
			else
			{
				lz_run = Shift_Barrel(); lz_run<<=1;
				lz_run |= Shift_Barrel(); lz_run<<=1;
				lz_run |= Shift_Barrel(); lz_run += 5;
			}

			// DBFa
			lz_run++;

			// LZ copy
			while( lz_run-- )
			{
				out_buffer[ buf_ptr ] = out_buffer[ buf_ptr-lz_window ];
				fputc( out_buffer[ buf_ptr ], out_binary);
				buf_ptr++;
			}
			continue;
		} // end LZ/RLE

		// check stop flag
		if( Read_Byte(1)==0 ) break;
	} // end decoder

	//fwrite( buffer,1,buffer_ptr,out_binary );
}


void Decode_Start( int start )
{
	Cache_Buffer( start );
	Decode_Hybrid();

	printf( "\n[FILE] %X-%X", start, start+buffer_ptr );
}
