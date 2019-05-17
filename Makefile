#
# Source files section
#
SOURCE_WORTLISTE = source/wortliste/wortliste
SOURCE_SYNONYMLISTE = source/synonymliste/gistfile1.txt

#
# Compilation rules
#
german-pro-stemmer.far: german-pro-stemmer.grm wortliste.far synonymliste.far

wortliste.far: wortliste.grm wortliste

synonymliste.far: synonymliste.grm synonymliste

wortliste: $(SOURCE_WORTLISTE)
	cut -d\; -f1 $< > $@

synonymliste: $(SOURCE_SYNONYMLISTE)
	sed '/\(\S\+\) => \1/d' $< | sed 's/ => /\t/' > $@

clean:
	rm -f wortliste.far synonymliste.far wortliste synonymliste

%.far: %.grm
	thraxcompiler --input_grammar=$< --output_far=$@

