#
# Source files section
#
SOURCE_WORTLISTE = source/wortliste/wortliste
SOURCE_SYNONYMLISTE = source/synonymliste/gistfile1.txt
SOURCE_OFFO_HYPHENATION = source/offo-hyphenation/offo-hyphenation_v1.2.zip

#
# Compilation rules
#
german-pro-stemmer.far: german-pro-stemmer.grm wortliste.far synonymliste.far

byte.grm: /usr/local/share/thrax/grammars/byte.grm
	cp $< $@

util.far: util.grm byte.far

hyphenate.far: hyphenate.grm util.far

hyphenate.grm: $(SOURCE_OFFO_HYPHENATION) source/offo-hyphenation/offo2thrax-de.py
	python3 source/offo-hyphenation/offo2thrax-de.py $(SOURCE_OFFO_HYPHENATION) $@

test: hyphenate.far
	thraxrewrite-tester --far=$< --rules=HYPHENATE

diagram: hyphenate.far
	farextract $<
	fstdraw HYPHENATE > HYPHENATE.dot
	dot -Gdpi=2400 -Grankdir=LR -o HYPHENATE.png -Tpng HYPHENATE.dot
	rm HYPHENATE.dot HYPHENATE

wortliste.far: wortliste.grm wortliste

synonymliste.far: synonymliste.grm synonymliste

wortliste: $(SOURCE_WORTLISTE)
	cut -d\; -f1 $< > $@

synonymliste: $(SOURCE_SYNONYMLISTE)
	sed '/\(\S\+\) => \1/d' $< | sed 's/ => /\t/' > $@

clean:
	rm -f hyphenate.far wortliste.far synonymliste.far hyphenate.grm wortliste synonymliste

%.far: %.grm
	thraxcompiler --input_grammar=$< --output_far=$@

