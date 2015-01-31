#!/usr/bin/perl

use Time::HiRes qw(usleep ualarm);
use IO::Socket::SSL;
use strict;
use warnings;

my $port = "/dev/ttyUSB0";
my $line;

open (SERIALPORT, "+<", "$port") or die "can't open $port. ";
usleep(100000);

$SIG{ALRM} = sub {
    print "!!!!Time OUT restart the unit!!!!\n";
};
print "READY\r\n";

while( $line = <SERIALPORT>)  {
	#print $line;
	  if( $line =~ /FreeRTOS/ ) {
		  print "begin\r\n";
		  print SERIALPORT "boot\r\n";
		  usleep(1_000_000);
	  }
	  if( $line =~ /SSID RSSI UNIQUE/ ) {
		  print SERIALPORT "connect hello-prov myfunnypassword 2\r\n";
		  usleep(1_000_000);
          }
	  if( $line =~ /SL_NETAPP_IPV4_ACQUIRED/) {
		#  print SERIALPORT "loglevel 40\r\n";
		  usleep(1_000_000);

		  print SERIALPORT "testkey\r\n";
		  usleep(1_000_000);
		  ualarm(20_000_000);
	  }
	  if( $line =~ /factory key: ([0-9A-Z]+)/ ) {
		  my $key = $1;

		  print "_____,-*^ Scan serial ^*-,_____\r\n";
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
			  print "Testing\r\n";
			  print SERIALPORT "testkey\r\n";
			  usleep(1_000_000);
			  ualarm(20_000_000);
		  } else {
			  print "failed to provision\n";
		  }
		  close($cl);
	  }
	  if( $line =~ /Test key failed: network error/ ) {
		  print "connection failed, retrying\r\n";
		  print SERIALPORT "testkey\r\n";
		  usleep(1_000_000);
	  }
	  if( $line =~ / test key success/ ) {
	          ualarm(0);
		  print SERIALPORT "disconnect\r\n";
		  usleep(1_000_000);
		  print "----------SUCCESS------------\r\n";
	  }
	  if( $line =~ /test key not valid/ ) {
	          ualarm(0);
		  print "test key failed, generating key...\r\n";
		  print SERIALPORT "genkey\r\n";
		  usleep(1_000_000);
	  }
}

