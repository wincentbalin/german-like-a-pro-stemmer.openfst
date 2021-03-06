#
# Source files section
#
SOURCE_WORTLISTE = source/wortliste/wortliste
SOURCE_SYNONYMLISTE = source/synonymliste/gistfile1.txt
SOURCE_OFFO_HYPHENATION = source/offo-hyphenation/offo-hyphenation_v1.2.zip
SOURCE_HUNSPELL_INFLECTED = source/hunspell-dict/inflected/hunspell-inflected.txt

#
# Compilation rules
#
german-pro-stemmer.far: german-pro-stemmer.grm synonymliste.far primary-word.far hunspell-stems.far

primary-word.far: primary-word.grm hyphenate.far wortliste.far symbols.far

hyphenate.far: hyphenate.grm symbols.far

hyphenate.grm: $(SOURCE_OFFO_HYPHENATION) source/offo-hyphenation/offo2thrax-de.py
	python3 source/offo-hyphenation/offo2thrax-de.py $(SOURCE_OFFO_HYPHENATION) $@

hyphenate-test: hyphenate.far
	thraxrewrite-tester --input_mode=utf8 --output_mode=utf8 --far=$< --rules=HYPHENATE

hyphenate-diagram: hyphenate.far
	farextract $<
	fstdraw HYPHENATE > HYPHENATE.dot
	dot -Gdpi=2400 -Grankdir=LR -o HYPHENATE.png -Tpng HYPHENATE.dot
	rm HYPHENATE.dot HYPHENATE

hunspell-stems.far: hunspell-stems.grm hunspell-stems symbols.far

wortliste.far: wortliste.grm wortliste

synonymliste.far: synonymliste.grm synonymliste symbols.far

hunspell-stems: $(SOURCE_HUNSPELL_INFLECTED)
	grep -P -e '\t-' $< | grep -v -e '-$$' > $@

wortliste: $(SOURCE_WORTLISTE)
	cut -d\; -f1 $< > $@

synonymliste: $(SOURCE_SYNONYMLISTE)
	sed '/\(\S\+\) => \1/d' $< | sed 's/ => /\t/' | sed 's/.$$//' > $@

clean:
	rm -f *.far hyphenate.grm wortliste synonymliste hunspell-stems

%.far: %.grm
	thraxcompiler --input_grammar=$< --output_far=$@

