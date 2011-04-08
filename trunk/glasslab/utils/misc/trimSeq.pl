#!/usr/bin/perl -w
if (@ARGV < 1) {
	print STDERR "<fastq file>\n";
	exit;
}

my %trim =();
my $minLength = 10;
my $c = 0;
my $good = 1;
my $id = '';
my $seq = '';
my $qual = '';
open IN, $ARGV[0];
while (<IN>) {
	chomp;
	if (/^\@(.*?)$/) {
		$c=0;
		$good = 1;
		$id = $1;
		next;
	} elsif (/^\+(.*?)$/) {
		if ($id ne $1) {
			$good = 0 
		}
		$c++;
	} else {
		if ($c == 0) {
			$seq = $_;
		} elsif ($c == 2) {
			$qual = $_;
			if ($good == 1) {

#				my $og = length($seq);
#print STDERR "$seq\n";
				$seq =~ s/[AN]+$//;
#print STDERR "$seq\n\n";
				my $L = length($seq);
#				my $diff = $og -$L;
				$trim{$L}++;
next if ($L < $minLength);
				
				$qual = substr($qual, 0, $L);
				print "@" . "$id\n$seq\n" . "+" . "$id\n$qual\n";

			}
		}
		$c++;
	}
		

}
close IN;

my @trims = sort {$a <=> $b} keys %trim;
foreach(@trims) {
	print STDERR "$_\t$trim{$_}\n";
}
