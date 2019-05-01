#
# Source files section
SOURCE_WORTLISTE = source/wortliste/wortliste
SOURCE_SYNONYMLISTE = source/synonymliste/gistfile1.txt

german-pro-stemmer.far: german-pro-stemmer.grm wortliste synonymliste
	thraxcompiler --input_grammar=$< --output_far=$@

wortliste: $(SOURCE_WORTLISTE)
	cut -d\; -f1 $< > $@

synonymliste: $(SOURCE_SYNONYMLISTE)
	sed '/\(\S\+\) => \1/d' $< | sed 's/ => /\t/' > $@

clean:
	rm -f wortliste synonymliste
