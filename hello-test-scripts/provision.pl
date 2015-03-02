#!/usr/bin/perl

use Time::HiRes qw(usleep ualarm);
use IO::Socket::SSL;
use Term::ANSIColor qw(:constants);
use strict;
use warnings;

use read_serial;

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

sub slow_type{
    my ($str) = @_;
    for my $char (split //, $str){
        print SERIALPORT $char;
        usleep(1_000);
    }
}
$SIG{ALRM} = sub {
`clear`;
print RED, "


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


", RESET;
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
		  print YELLOW, "


####### #######  #####  #######         ######  #######  #####    ###   #     #
   #    #       #     #    #            #     # #       #     #    #    ##    #
   #    #       #          #            #     # #       #          #    # #   #
   #    #####    #####     #            ######  #####   #  ####    #    #  #  #
   #    #             #    #            #     # #       #     #    #    #   # #
   #    #       #     #    #            #     # #       #     #    #    #    ##
   #    #######  #####     #            ######  #######  #####    ###   #     #


", RESET;
          slow_type("\r\nboot\r\n");
          slow_type("\r\ndisconnect\r\n");
          slow_type("\r\n^ pause\r\n");
          slow_type("\r\nprovision\r\n");
	  }
	  if( $line =~ /PAIRING MODE/ ) {
          ualarm(0);
        slow_type("\r\nconnect hello-prov myfunnypassword 2\r\n");
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
		  ualarm(0);
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
          usleep(4_000_000);
          slow_type("\r\ntestkey\r\n");
		  ualarm(70_000_000);
	  }
	  if( $line =~ /factory key: ([0-9A-Z]+)/ ) {
          ualarm(0);
		  my $key = $1;
`clear`;
		  print BLUE,"
 ##### 
#     #   ####     ##    #    #
#        #    #   #  #   ##   #
 #####   #       #    #  # #  #
      #  #       ######  #  # #
#     #  #    #  #    #  #   ##
 #####    ####   #    #  #    #

 #####
#     #  ######  #    #   ####   ######
#        #       ##   #  #       #
 #####   #####   # #  #   ####   #####
      #  #       #  # #       #  #
#     #  #       #   ##  #    #  #
 #####   ######  #    #   ####   ######

 #####
#     #  ######  #####      #      ##    #
#        #       #    #     #     #  #   #
 #####   #####   #    #     #    #    #  #
      #  #       #####      #    ######  #
#     #  #       #   #      #    #    #  #
 #####   ######  #    #     #    #    #  ######


", RESET;
		  my $serial = read_serial();
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
			  usleep(4_000_000);
              slow_type("\r\ntestkey\r\n");
			  ualarm(20_000_000);
		  } else {
`clear`;

			  print RED, "


#######    #      ###   #
#         # #      #    #
#        #   #     #    #
#####   #     #    #    #
#       #######    #    #
#       #     #    #    #
#       #     #   ###   #######


", RESET;
		  }
		  close($cl);
	  }
	  if( $line =~ / test key success/ ) {
          ualarm(0);
          slow_type("\r\nloglevel 40\r\ndisconnect\r\n");
          my $got_region = 0;
          
          while( !$got_region ) { #disable for demo
          
          print BLUE,"

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
             \\m___m__|_|    \\m_m_|   \\mm_|

", RESET;

          my $upc = <>;
          chomp($upc);
          print "Got UPC ".$upc.".\r\n";
          
          # if (0) { # enable for demo
          
          if( exists $region_map{$upc}  ) {
              print "Setting country code ",$region_map{$upc},"\n";
              slow_type("\r\ncountry ",$region_map{$upc},"\r\n");
              $got_region = 1;
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
          }
        }
          
          #check the pill
          my $good_pill = 1;
          
          while( !$good_pill) {
              print "
              
 #####
#     #   ####     ##    #    #
#        #    #   #  #   ##   #
 #####   #       #    #  # #  #
      #  #       ######  #  # #
#     #  #    #  #    #  #   ##
 #####    ####   #    #  #    #

######
#     #     #    #       #
#     #     #    #       #
######      #    #       #
#           #    #       #
#           #    #       #
#           #    ######  ######
              
              ";
            my $serial = read_serial();
            chomp($serial);
            print "Got serial ".$serial.".\r\n";

            my $post = "GET /v1/provision/check/p/".$serial." HTTP/1.1\r\n".
            "Host: provision.hello.is\r\n".
            "Content-type: text/plain\r\n".
            "Accept: */*\r\n".
            "\r\n";

            my $cl = IO::Socket::SSL->new('provision.hello.is:443');

            #print $post;
            print $cl $post;


            my $response = <$cl>;
            #print "Reply:\r\n".$response;

            if( $response =~ /200 OK/ ) {
                $good_pill = 1;
            } else {
                print "
                
                #######
                #          ##       #    #
                #         #  #      #    #
                #####    #    #     #    #
                #        ######     #    #
                #        #    #     #    #
                #        #    #     #    ######
                
                ######
                #     #     #    #       #
                #     #     #    #       #
                ######      #    #       #
                #           #    #       #
                #           #    #       #
                #           #    ######  ######
                
                ";
            }
          }
          
print GREEN, '
 ######     #     #####   #####  ####### ######
 #     #   # #   #     # #     # #       #     #
 #     #  #   #  #       #       #       #     #
 ######  #     #  #####   #####  #####   #     #
 #       #######       #       # #       #     #
 #       #     # #     # #     # #       #     #
 #       #     #  #####   #####  ####### ######
', RESET;
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
          slow_type("\r\ngenkey\r\n");
          ualarm(20_000_000);
	  }
}

