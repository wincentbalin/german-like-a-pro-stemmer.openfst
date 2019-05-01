#
# Source files section
SOURCE_WORTLISTE = source/wortliste/wortliste
SOURCE_SYNONYMLISTE = source/synonymliste/gistfile1.txt

wortliste: $(SOURCE_WORTLISTE)
	cut -d\; -f1 $< > $@

synonymliste: $(SOURCE_SYNONYMLISTE)
	sed '/\(\S\+\) => \1/d' $< | sed 's/ => /\t/' > $@

german-pro-stemmer.far: german-pro-stemmer.grm wortliste synonymliste
	thraxcompiler --input_grammar=$< --output_far=$@

clean:
	rm -f wortliste synonymliste
