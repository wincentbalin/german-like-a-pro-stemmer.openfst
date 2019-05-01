#
# Source files section
SOURCE_WORTLISTE = source/wortliste/wortliste

wortliste: $(SOURCE_WORTLISTE)
	cut -d\; -f1 $< > $@

german-pro-stemmer.far: german-pro-stemmer.grm wortliste1
	thraxcompiler --input_grammar=$< --output_far=$@

clean:
	rm -f wortliste
