#!/usr/bin/perl

use Time::HiRes qw(usleep ualarm);
use IO::Socket::SSL;
use strict;
use warnings;

my $port = "/dev/ttyUSB0";
my $line;

my %region_map = (
"040232206634" => "US",
"040232206641" => "US",
"040232206658" => "EU",
"040232206665" => "EU",
"040232206672" => "EU",
"040232206580" => "EU",
"040232206597" => "EU",
"040232206603" => "EU",
);

`stty -brkint -icrnl ixoff -imaxbel -opost -onlcr -isig -icanon -F /dev/ttyUSB0 115200`;

open (SERIALPORT, "+<", "$port") or die "can't open $port. ";
usleep(100000);

$SIG{ALRM} = sub {
`clear`;
print "


#######   ###   #     # ####### ####### #     # #######
   #       #    ##   ## #       #     # #     #    #
   #       #    # # # # #       #     # #     #    #
   #       #    #  #  # #####   #     # #     #    #
   #       #    #     # #       #     # #     #    #
   #       #    #     # #       #     # #     #    #
   #      ###   #     # ####### #######  #####     #

######  #######    #    ####### #######    #     #####  #     #
#     # #         # #      #       #      # #   #     # #     #
#     # #        #   #     #       #     #   #  #       #     #
######  #####   #     #    #       #    #     # #       #######
#   #   #       #######    #       #    ####### #       #     #
#    #  #       #     #    #       #    #     # #     # #     #
#     # ####### #     #    #       #    #     #  #####  #     #


";
};
`clear`;
print "


   #    ####### #######    #     #####  #     #         #     # ####### #     #
  # #      #       #      # #   #     # #     #         ##    # #       #  #  #
 #   #     #       #     #   #  #       #     #         # #   # #       #  #  #
#     #    #       #    #     # #       #######         #  #  # #####   #  #  #
#######    #       #    ####### #       #     #         #   # # #       #  #  #
#     #    #       #    #     # #     # #     #         #    ## #       #  #  #
#     #    #       #    #     #  #####  #     #         #     # #######  ## ##


######  ####### #     #   ###    #####  #######
#     # #       #     #    #    #     # #
#     # #       #     #    #    #       #
#     # #####   #     #    #    #       #####
#     # #        #   #     #    #       #
#     # #         # #      #    #     # #
######  #######    #      ###    #####  #######


";

while( $line = <SERIALPORT>)  {
	#print $line;
	  if( $line =~ /FreeRTOS/ ) {
`clear`;
		  print "


####### #######  #####  #######         ######  #######  #####    ###   #     #
   #    #       #     #    #            #     # #       #     #    #    ##    #
   #    #       #          #            #     # #       #          #    # #   #
   #    #####    #####     #            ######  #####   #  ####    #    #  #  #
   #    #             #    #            #     # #       #     #    #    #   # #
   #    #       #     #    #            #     # #       #     #    #    #    ##
   #    #######  #####     #            ######  #######  #####    ###   #     #


";
		  print SERIALPORT "disconnect\r\n";
		  print SERIALPORT "boot\r\n";
		  usleep(1_000_000);
	  }
	  if( $line =~ /PAIRING MODE/ ) {
		usleep(1_000_000);		  
		print SERIALPORT "connect hello-prov myfunnypassword 2\r\n";
`clear`;
		  print "


 #####  ####### #     # #     # #######  #####  #######   ###   #     #  #####
#     # #     # ##    # ##    # #       #     #    #       #    ##    # #     #
#       #     # # #   # # #   # #       #          #       #    # #   # #
#       #     # #  #  # #  #  # #####   #          #       #    #  #  # #  ####
#       #     # #   # # #   # # #       #          #       #    #   # # #     #
#     # #     # #    ## #    ## #       #     #    #       #    #    ## #     #
 #####  ####### #     # #     # #######  #####     #      ###   #     #  #####


";

		  ualarm(20_000_000);
         }
	  if( $line =~ /SL_NETAPP_IPV4_ACQUIRED/) {
		  usleep(1_000_000);
`clear`;
		  print "


####### #######  #####  #######   ###   #     #  #####
   #    #       #     #    #       #    ##    # #     #
   #    #       #          #       #    # #   # #
   #    #####    #####     #       #    #  #  # #  ####
   #    #             #    #       #    #   # # #     #
   #    #       #     #    #       #    #    ## #     #
   #    #######  #####     #      ###   #     #  #####


";
		  print SERIALPORT "testkey\r\n";
		  usleep(1_000_000);
		  ualarm(20_000_000);
	  }
	  if( $line =~ /factory key: ([0-9A-Z]+)/ ) {
		  my $key = $1;
`clear`;
		  print "
                                                                 .---.
                                                                /  .  \
                                                               |\_/|   |
                                                               |   |  /|
    -----------------------------------------------------------------  |
   /  .-.                                                              |
  |  /   \        #####   #####     #    #     #                       |
  | |\_.  |      #     # #     #   # #   ##    #                       |
  |\|  | /|      #       #        #   #  # #   #                       |
  |  ---  |       #####  #       #     # #  #  #                       |
  |       |            # #       ####### #   # #                       |
  |       |      #     # #     # #     # #    ##                       |
  |       |       #####   #####  #     # #     #                       |
  |       |                                                            |
  |       |      #####  ####### ######    ###      #    #              |
  |       |     #     # #       #     #    #      # #   #              |
  |       |     #       #       #     #    #     #   #  #              |
  |       |      #####  #####   ######     #    #     # #              |
  |       |           # #       #   #      #    ####### #              |
  |       |     #     # #       #    #     #    #     # #              |
  |       |      #####  ####### #     #   ###   #     # #######        |
  |       |                                                            |
  |       |                                                           /
  |       |----------------------------------------------------------|
   \       |
    \____ /

";
		  my $serial = <>;
		  chomp($serial);
		  print "Got serial ".$serial.".\r\n";
		  
		  my $post = "POST /v1/provision/".$serial." HTTP/1.0\r\n".
		  "Host: provision.hello.is\r\n".
		  "Content-type: text/plain\r\n".
		  "Content-length: ".length($key)."\r\n".
		  "\r\n".
		  $key;
		  #print $post;

		  my $cl = IO::Socket::SSL->new('provision.hello.is:443');
		  print $cl $post;

		  my $response = <$cl>;
		  #print "Reply:\r\n".$response;
		  
		  if( $response =~ /200 OK/ ) {
			  # Allocate MAC?
`clear`;
		  print "


####### #######  #####  #######   ###   #     #  #####
   #    #       #     #    #       #    ##    # #     #
   #    #       #          #       #    # #   # #
   #    #####    #####     #       #    #  #  # #  ####
   #    #             #    #       #    #   # # #     #
   #    #       #     #    #       #    #    ## #     #
   #    #######  #####     #      ###   #     #  #####


";
			  usleep(1_000_000);
			  print SERIALPORT "testkey\r\n";
			  usleep(1_000_000);
			  ualarm(20_000_000);
		  } else {
`clear`;

			  print "


#######    #      ###   #
#         # #      #    #
#        #   #     #    #
#####   #     #    #    #
#       #######    #    #
#       #     #    #    #
#       #     #   ###   #######


";
		  }
		  close($cl);
	  }
	  if( $line =~ /Test key failed: network error/ ) {
`clear`;

		  print "


####### #######  #####  #######   ###   #     #  #####
   #    #       #     #    #       #    ##    # #     #
   #    #       #          #       #    # #   # #
   #    #####    #####     #       #    #  #  # #  ####
   #    #             #    #       #    #   # # #     #
   #    #       #     #    #       #    #    ## #     #
   #    #######  #####     #      ###   #     #  #####


";
		  print SERIALPORT "testkey\r\n";
		  usleep(1_000_000);
	  }
	  if( $line =~ / test key success/ ) {
	          ualarm(0);
		  print SERIALPORT "loglevel 40\r\ndisconnect\r\n";

          my $got_region = 0;
          
          while( !$got_region ) {
          
          print "

 #####                                  #     # ######   #####
#     #   ####     ##    #    #         #     # #     # #     #
#        #    #   #  #   ##   #         #     # #     # #
 #####   #       #    #  # #  #         #     # ######  #
      #  #       ######  #  # #         #     # #       #
#     #  #    #  #    #  #   ##         #     # #       #     #
 #####    ####   #    #  #    #          #####  #        #####
 
           _____
          /     \
          vvvvvvv  /|__/|
             I   /O,O   |
             I /_____   |      /|/|
            J|/^ ^ ^ \  |    /00  |    _//|
             |^ ^ ^ ^ |W|   |/^^\ |   /oo |
             \\m___m__|_|   \\m_m_|  \\mm_|
          
          ";
          my $upc = <>;
          chomp($upc);
          print "Got UPC ".$upc.".\r\n";
          
          if( exists $region_map{$upc}  ) {
              print "Setting country code ",region_map{$upc},"\n";
              print SERIALPORT "country ",region_map{$upc},"\n";
          } else {
              print "
              
#######
#        #####   #####    ####   #####
#        #    #  #    #  #    #  #    #
#####    #    #  #    #  #    #  #    #
#        #####   #####   #    #  #####
#        #   #   #   #   #    #  #   #
#######  #    #  #    #   ####   #    #

#     #
#     #  #    #  #    #  #    #   ####   #    #  #    #
#     #  ##   #  #   #   ##   #  #    #  #    #  ##   #
#     #  # #  #  ####    # #  #  #    #  #    #  # #  #
#     #  #  # #  #  #    #  # #  #    #  # ## #  #  # #
#     #  #   ##  #   #   #   ##  #    #  ##  ##  #   ##
 #####   #    #  #    #  #    #   ####   #    #  #    #

              #     # ######   #####
              #     # #     # #     #
              #     # #     # #
              #     # ######  #
              #     # #       #
              #     # #       #     #
               #####  #        #####


          ";
              $got_region = 1;
          }
        }

          
`clear`;

print '
@@@@8888888888888888888888888888880CG0G888@88888888800GL0CGG00CCGLG0G0C88888@@@@@@@@@@@@@@@@@@
@@@@88888888888888888888888880000G0088888888000GG0GLGLCfCCCLftfLfGCLCCGGC880@@@@@@@@@@@@@@@@@@
@@@888888888888888888888888888088088888800GCLftfGtf1fiiit;,:;i111tt1t1ffGG008@@@@@@@@@@@@@@@@@
@@@888888888888888888888888800888@888GLCCLLt;,,11:.:,          ..,,,,;11LGG0888@@@@@@@@@@@@@@@
@@@88888888888888888888888880088@@8GCCCfff1i;:,,....            ...,::;;;tG0000@@@@@@@@@@@@@@@
@@@8888888888888888888888888008@@@8GLLff1iiii;:,,.....         ..,,,,::::iLCC08@@@@@@@@@@@@@@@
@@8888888888888888888088888800@@@@80Lftt1ii;;::,,.........     ..,,,,,:;:iGGG00@@@@@@@@@@@@@@@
@@88888888888880888888888888008@@@88CLft11ii;;::,..,...    . ..,,,,,,:::;iG808@@@@@@@@@@@@@@@@
@@88888888888888888808888880000@@@@0CCft1iiiiiii;:::,,,.,,,,,,,,,,,,,,::;18888@@@@@@@@@@@@@@@@
@888888888088888888808888880000@@@8GCLf1ti;:;;;iiii;;;:::::::::::,,,,,:;ii88808@@@@@@@@@@@@@@@
@8888888888888888888088888800008@@0GCGG00G00GCCLLfftt11iii11ttfLGCCCLCt1;if8888@@@@@@@@@@@@@@@
@8888888800888888808088088800GGG88GCLCGGCLLCLLLfLLC:LftttfLLfffLffft11tLG111t08@@@@@@@@@@@@@@@
88888880800888800888088008800GGGG80CCLCCG8000000C0GGC1, ,LGCCCG0G08000CCL11C0C8@@@@@@@@@@@@@@@
88888888000088008080080008800GGCC0CLCCLGCCGG00CGGCGGt;. 1LG0GGCGCCGGGGGCt1LLC08@@@@@@@@@@@@@@@
8888888800008800008008008800GG0CG0CGCfCCCLftttffLL1f;,  .:1iti11ttt1i;:::ifff00@@@@@@@@@@@@@@@
888888880088800000000800080GGGGC80CCffft1i1i11;;fLti;,  .,fi,.,i;:,,,,,,:tff0008@@@@@@@@@@@@@@
8888880000088000000008000800GG0GC8GL11;:;iii;:;;itt;:.  .,,f1;:,,,,,,,,,;1G1G000@@@@@@@@@@@@@@
008088800008000000000800000GGG0008CLtfti:::::;11111i;.  .,:;fftii;i;;;i:ftGGG000@@@@8@@@@@@@@@
80088880008800000000000,   ,GG0088GCLLtti;:::::;f1tti,,,::,:;i;:,,::iffLftG000008@@@@@@@@@@@@@
00888000000800000000000L;   .GG0888GCLLtt11ii;::LCG0LffLG0C1::;i;;;;;;1ffGGGGG000@@@@@@@@@@@8@
008888000080000000008000f:,...G08@880LLLLffLi;;1CGGG0GG88Gf:,.,:i111itffL000GG000@@@@@@@@88@@@
008888000000000000008000Ci:...,088880GCLfL0GLLfLC0888880CGLft1;ifLftftfGGGGGG0000@@8@@@@@8@@@@
00880000000000000000800t1;::,,:08G88880Cff00GGGCCCCCLtfLLLLfffCLGCitLLC00CGCGGG00@888@8@@@@8@8
088800000080000008008L:,i;:,::;08G088880GLGGCCLLCGCCGGGGCGG0GCGGG1tCC088GGGGGGGG00@@@@88@88888
00880000000000000000:;;::;;:;i088GG08@@880800GCCCCG00000GCCCCtfG0GG80888GGCCGGGGGG888888888888
08880G000000G0000GG,::::;::;;1080G0008@@@8@8880GCG0888000LtfffC088888@080LCCLGGGGG@88@8888888@
8888GG00000000000...,.,::;;if0880000008@@@@@@880Ltf1ftttfttCG0888@@@80888LLLCCGCCG888888888888
0080G00000GG0G0.   .,,:i1t1f00880008808@@@@@@8880CLGCGCCLGGG08@@@@8@088888fLLLCCCC@88@88888888
0000G0000GGGG,.    :,,:;i;L888888888@@@@88@@@@8@80CG8C0G008888@@@880t18888LfffCCCCC88888888888
008GGG000CGL;,..           888088@@@@@@@00G0@@@@80GG888@88@8888800G1;:;iG0LLLfLLCGC88888888888
008CGGCCGCCi;,..                     G8@000GGG08@@@@8@@@@@880000Gfi;:,,::1CGCLCLLCC88888888888
CCCCCCGGGCi;::,,,......                  G00GGG00000000GGGGGGGGfii:,,,,LCGGGGGGCCCC08888888888
CCCCCCGGGii;;:::::,,,....      ....       .100000000000GGGGGC1;::,,:1GCCCCCGGGGCCCCCCL88888888
CGGGGCGi1t1ii;::,,,.. .....,,,,....          88888880000GGC1,.,,:GCCCCCCCC0GCGGCCCCLLLLLLLC888
GCGGCf:;11i;:::,,,,,. ...    .....:,,........,8888888000L:,,:GGCGGGCCCC80GGGCGGGCCLCLLCCCCCCCG
LGG1:,:;11i;:::::,,..           .:;i;;;;;:;:;G8888880Gfi,CCGCGGGCCLCC8GCGCCCCCGGCLLCCCCCCCLCCC
;;::,::;ii;;::::::,.                    .fC0GCCGCfi;:iGGGGGGGCCCCG0GCCCCCCCCGCCCCCCCCCLLCCCCCC
::;:,::;;;;;;;;;;;::,..                 .... CGGGCCGGGGGGGCCLLCG0GCCCLCCCCCCCCCCLCCLLLLLCLLCCL
:,:;:;;;;i11iiiiiii;;:.  .....,:,,:,,,,,,,::,,GCGGGGGGCCCLCCCGGGCCLCCCCCCCCCCLCLCCLLCLLCCLCCLC
;;::;;1111tt1111i1i;;:,,,,..:::::;::,:::::;;;1GGGCCCCCLCCCCGGCCCCCCCCCCCCCCCLLCLLCLLLLLCCLCLLL ######     #     #####   #####  ####### ######
;;;iii1tt1111i;i;;iiiiiiiii1iiii;;:::::::;itCCGCCLCCCCCCCCGCCCCCCCCCCCCCCCCCLLLLLCLLLLCGLLCLLC #     #   # #   #     # #     # #       #     #
iii11111t111ii;i;i;iii;;;;ii1iiiit111i11LCCCCCCCCGGCCCCCGGCCCCCCCCCCCCCCCCCLLLCLLLLLCLCCCCLCLC #     #  #   #  #       #       #       #     #
;iii11tt11t1t1i;iii;;:,,,,,,,:,..         .,CCCCCCGCCCCCCCCCCCCCCCCCCCCCCCCCCLCCCLLLLCLCCCLLCC ######  #     #  #####   #####  #####   #     #
ii;i11tf111iiiiiii;::,,.     ............,:,GGCCCCCGCCCCCCCCCCCCCCCCCCCCCCCCCCCCLLLLLCCCLCLfLC #       #######       #       # #       #     #
i;;ii1Lfftiii1iii;;:,..     ..,,,,::::;;iii1GGCCCCGCGCCCCCCCCCCCCCCCCCCCCCCCCCLLLLCCCCCCLLLLCC #       #     # #     # #     # #       #     #
;ii;i1tfft1i;ii111i;:,.,,,,:::;;i;iiii11tfC0GGCCGCCCCCCLCLCCCCCCCCCCCCCCCCCCCLLLCLCLCCCLLLLGCC #       #     #  #####   #####  ####### ######
1t1t1ttffff11iii1ttti;:::::iii11i1iii1fLGGG00GCCCCCCCCCCCCCCCCCCCCCCCCCCCCLLLLLLLLCLCCCLCCGCCC
1111ttfLfffft1111ttttti;;i1111LCfiii1fLGGGG000CCCCCCCCCCCCCCGCCCCCCCCCCCCLCCLCLLLCCCCCCL00GCGG
f11111fCLLfffftt1t11iiii;;::::....,,:;1GCGGG00GGGCCCCCCCCCCCCCCGCCCCCLLCCCCCCCCCCCCCCCLL0GGGGC
ttG080ftLLLfffftt1i;;::;:::::;;i:;ifLGGGGGGGGG0GGCCCCCCCCGCCCCGCCCCCCCCCCLLCCLLCCCCCCCCC0GCCCC
88888080LLLffffft1ii:,::;ii111i1tfCGGGGGGGGGG0GGGGGGCCCGCCCCCCGCCCCCCCCLCLLLLCCCCCCCCCCCGG0GLG
8888888088ffftfftt11iiiittttttf0GGGGGGGGCGGGGGGG0GGCGCGCGCCGCCCCCCLCLCCLCCCCLCCCCCCCCCCC0GLCGG
88800880888800ftff11111ttL8888000GGGGGCCGCCCCGGGGGCCCCCCCCLCCCLCCCLCLCCCCCCCLCCLLCCCCCCCGCGGC
';
	  }
	  if( $line =~ /test key not valid/ ) {
	          ualarm(0);
`clear`;

		  print "


 #####  ####### #     # ####### ######     #    #######   ###   #     #  #####
#     # #       ##    # #       #     #   # #      #       #    ##    # #     #
#       #       # #   # #       #     #  #   #     #       #    # #   # #
#  #### #####   #  #  # #####   ######  #     #    #       #    #  #  # #  ####
#     # #       #   # # #       #   #   #######    #       #    #   # # #     #
#     # #       #    ## #       #    #  #     #    #       #    #    ## #     #
 #####  ####### #     # ####### #     # #     #    #      ###   #     #  #####


#    #  ####### #     #
#   #   #        #   #
#  #    #         # #
###     #####      #
#  #    #          #
#   #   #          #
#    #  #######    #


";
		  usleep(1_000_000);
		  print SERIALPORT "genkey\r\n";
		  usleep(1_000_000);
	  }
}

