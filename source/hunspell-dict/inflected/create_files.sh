#!/bin/bash
# Extract affix and dictionary file
unzip -c -q ../dict-de_de-frami_2017-01-12.oxt de_DE_frami/de_DE_frami.aff | iconv -f ISO8859-1 -t UTF-8 > de_DE_frami.aff
sed -i -e s/ISO8859-1/UTF-8/ de_DE_frami.aff
unzip -c -q ../dict-de_de-frami_2017-01-12.oxt de_DE_frami/de_DE_frami.dic | iconv -f ISO8859-1 -t UTF-8 > de_DE_frami.dic
# Download wordforms utility from Hunspell repository
wget -O wordforms `cat wordforms-source.txt`
chmod 0755 wordforms
# Created root-inflected pairs
./wordforms_inflected de_DE_frami.aff de_DE_frami.dic UTF-8 | tee hunspell-inflected-dup.txt
# Deduplicate root-inflected pairs
cat hunspell-inflected-dup.txt | sort | uniq > hunspell-inflected.txt
# Filter only word forms at the end of a compound word
grep -e '\t-' hunspell-inflected.txt | grep -v -e '-$' > hunspell-stems.txt

