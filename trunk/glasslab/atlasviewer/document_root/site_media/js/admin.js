var select_codon_highlighting = function() {
	if (django.jQuery('#id_strand')[0].value == '0') {
		// Show only sense codon coloring
		django.jQuery('.antisense-stop-codon').removeClass('antisense-stop-codon');
		django.jQuery('.antisense-start-codon').removeClass('antisense-start-codon');
	} else {
		// Show only antisense codon coloring
		django.jQuery('.stop-codon').removeClass('stop-codon');
		django.jQuery('.start-codon').removeClass('start-codon');
	};
};