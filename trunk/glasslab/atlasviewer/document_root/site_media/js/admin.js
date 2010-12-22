var select_codon_highlighting = function() {
	if (django.jQuery('#id_strand')[0].value == '0') {
		// Show only sense codon coloring
		django.jQuery('.antisense-sequence').hide();
	} else {
		// Show only antisense codon coloring
		django.jQuery('.sense-sequence').hide();
	};
};

var fill_length = function() {
	django.jQuery('#length-message').text(
		'Length: ' +
		(django.jQuery('#id_transcription_end')[0].value -
			django.jQuery('#id_transcription_start')[0].value) 
	);

};