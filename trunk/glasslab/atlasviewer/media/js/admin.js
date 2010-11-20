var highlight_stop_codons = function() {
	django.jQuery('.sequence').html(
		django.jQuery('.sequence').html().replace('TAA','<span class="stop-codon">TAA</span>')
		);
	django.jQuery('.sequence').html(
		django.jQuery('.sequence').html().replace('TAG','<span class="stop-codon">TAA</span>')
		);
	django.jQuery('.sequence').html(
		django.jQuery('.sequence').html().replace('TGA','<span class="stop-codon">TAA</span>')
		);
};