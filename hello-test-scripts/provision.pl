#!/usr/bin/perl

use Time::HiRes qw(usleep ualarm);
use IO::Socket::SSL;
use Term::ANSIColor qw(:constants);
use strict;
use warnings;

use read_serial;

my $port = "/dev/ttyUSB0";
my $logfile = "station.log";
my $version = "v3";
my $line;
my $killswitch = 0;
my $has200 = 0;


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
open (LOG, ">>", $logfile) or die "can't open $logfile. ";
usleep(100000);

sub slow_type{
    my ($str) = @_;
    if ($killswitch == 0){
        for my $char (split //, $str){
            print SERIALPORT $char;
            usleep(1_000);
        }
    }
}
sub print_generating_key{
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
}
sub print_scan_upc{
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
}
sub print_testing{
		  print "
####### #######  #####  #######   ###   #     #  #####
   #    #       #     #    #       #    ##    # #     #
   #    #       #          #       #    # #   # #
   #    #####    #####     #       #    #  #  # #  ####
   #    #             #    #       #    #   # # #     #
   #    #       #     #    #       #    #    ## #     #
   #    #######  #####     #      ###   #     #  #####
";
}
sub print_connecting{
		  print "
 #####  ####### #     # #     # #######  #####  #######   ###   #     #  #####
#     # #     # ##    # ##    # #       #     #    #       #    ##    # #     #
#       #     # # #   # # #   # #       #          #       #    # #   # #
#       #     # #  #  # #  #  # #####   #          #       #    #  #  # #  ####
#       #     # #   # # #   # # #       #          #       #    #   # # #     #
#     # #     # #    ## #    ## #       #     #    #       #    #    ## #     #
 #####  ####### #     # #     # #######  #####     #      ###   #     #  #####
";
}
sub print_fail{
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
sub print_scan_sense_serial{
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
}
sub print_pass{
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
sub print_test_begin{
		  print YELLOW, "


####### #######  #####  #######         ######  #######  #####    ###   #     #
   #    #       #     #    #            #     # #       #     #    #    ##    #
   #    #       #          #            #     # #       #          #    # #   #
   #    #####    #####     #            ######  #####   #  ####    #    #  #  #
   #    #             #    #            #     # #       #     #    #    #   # #
   #    #       #     #    #            #     # #       #     #    #    #    ##
   #    #######  #####     #            ######  #######  #####    ###   #     #


", RESET;
}
sub print_unknown_upc{
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
$SIG{ALRM} = sub {
$killswitch = 1;
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
sub verify_sn{
    return 1;
}
while( 1 ) {
    my $uut_sn;
    print_scan_sense_serial();
    $uut_sn = read_serial();
    $session_logfile = "./session/$uut_sn"."_".time().".log";
    open (SESSION, ">>", $session_logfile) or die "can't open $session_logfile. ";
    #region
    my $got_region = 0;
    my $upc;
    while( !$got_region ) { #disable for demo
        `clear`;
        print_scan_upc();
        $upc = <>;
        chomp($upc);
        print SESSION "Got UPC ".$upc.".\r\n";
        if( exists $region_map{$upc}  ) {
            $got_region = 1;
        } else {
            print_unknown_upc();
        }
    }
    while( $line = <SERIALPORT>)  {
        print SESSION "[$time, $version] $line";
        if( $line =~ /FreeRTOS/ ) {
            `clear`;
            print SESSION "Command: country code ",$region_map{$upc},"\n";
            slow_type("\r\ncountry ",$region_map{$upc},"\r\n");
            slow_type("\r\nboot\r\n");
            slow_type("\r\ndisconnect\r\n");
            slow_type("\r\n^ pause\r\n");
        }
        if( $line =~ "Boot completed" ){
            `clear`;
            slow_type("\r\ngenkey\r\n");
            print SESSION "Command: genkey\n";
            print_generating_key();
        }
        if( $line =~ /factory key: ([0-9A-Z]{256})/ ) {
            `clear`;
            ualarm(0);
            my $key = $1;
            my $post = "POST /v1/provision/".$uut_sn." HTTP/1.0\r\n".
            "Host: provision.hello.is\r\n".
            "Content-type: text/plain\r\n".
            "Content-length: ".length($key)."\r\n".
            "\r\n".
            $key;
            print SESSION "Post: $post\n";

            my $cl = IO::Socket::SSL->new('provision.hello.is:443');
            print $cl $post;

            my $response = <$cl>;
            print SESSION "Response: $response\n"

            if( $response =~ /200 OK/ ) {
                print SESSION "Passed Provisioning\n";
                print_pass();
            } else {
                print SESSION "Failed Provisioning\n";
                print_fail();
            }
            close($cl);
            close(SESSION);
            `./sanders pch $session_logfile &`
        }
    }
}
