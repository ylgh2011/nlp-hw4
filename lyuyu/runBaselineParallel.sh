#!/bin/bash

PIDs=""
inputIndexes=( 1 2 3 4 5 6 7 8 )

mkdir output
for i in "${inputIndexes[@]}"; do
	python baseline.py -s 15000 -k 50 -d 12 -a 0.9 -i data/input$i > output/output$i
	PIDs="$PIDs $!"
done
wait $PIDs

for i in "${inputIndexes[@]}"; do
	cat output/output$i >> output/output_all.txt
done

echo "Done, all outputs are merged into output/output_all.txt"

