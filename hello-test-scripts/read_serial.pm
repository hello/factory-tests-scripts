package read_serial;
use strict;
use warnings;
use Exporter;

our @ISA= qw( Exporter );

# these CAN be exported.
our @EXPORT_OK = qw( read_serial );

# these are exported by default.
our @EXPORT = qw( read_serial );

sub read_serial {
    while(1) {
        #910000082B01145000123
        if( <> =~ /^[A-Z0-9]{21}$/ ) {
            print "Got serial ",$&,"\n";
            chomp($&);
            return $&;
        } else {
            print "INVALID serial ",$&,"\n";
        }
    }
}

1;