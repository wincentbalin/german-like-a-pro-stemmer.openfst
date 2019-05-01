german-pro-stemmer.far: german-pro-stemmer.grm wortliste1
	thraxcompiler --input_grammar=$< --output_far=$@

clean:
	rm -f 
