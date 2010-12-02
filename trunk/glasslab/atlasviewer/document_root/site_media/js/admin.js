var select_codon_highlighting = function() {
	if (django.jQuery('#id_strand')[0].value == '0') {
		// Show only sense codon coloring
		django.jQuery('.antisense-sequence').hide();
	} else {
		// Show only antisense codon coloring
		django.jQuery('.sense-sequence').hide();
	};
};