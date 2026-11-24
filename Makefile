.PHONY: all curriculum-map volume-1 volume-2 volume-3 volume-4 volume-5 master clean

all: curriculum-map volume-1 volume-2 volume-3 volume-4 volume-5 master

curriculum-map:
	@echo "==> Compiling curriculum-map.pdf..."
	cd latex/curriculum-map && pdflatex -interaction=nonstopmode curriculum-map.tex && pdflatex -interaction=nonstopmode curriculum-map.tex
	cp latex/curriculum-map/curriculum-map.pdf ./curriculum-map.pdf

volume-1:
	@echo "==> Compiling volume-1-backend.pdf..."
	cd latex/volume-1 && pdflatex -interaction=nonstopmode volume-1.tex && pdflatex -interaction=nonstopmode volume-1.tex
	cp latex/volume-1/volume-1.pdf ./volume-1-backend.pdf

volume-2:
	@echo "==> Compiling volume-2-ai-engineering.pdf..."
	cd latex/volume-2 && pdflatex -interaction=nonstopmode volume-2.tex && pdflatex -interaction=nonstopmode volume-2.tex
	cp latex/volume-2/volume-2.pdf ./volume-2-ai-engineering.pdf

volume-3:
	@echo "==> Compiling volume-3-cloud-devsecops.pdf..."
	cd latex/volume-3 && pdflatex -interaction=nonstopmode volume-3.tex && pdflatex -interaction=nonstopmode volume-3.tex
	cp latex/volume-3/volume-3.pdf ./volume-3-cloud-devsecops.pdf

volume-4:
	@echo "==> Compiling volume-4-distributed-systems.pdf..."
	cd latex/volume-4 && pdflatex -interaction=nonstopmode volume-4.tex && pdflatex -interaction=nonstopmode volume-4.tex
	cp latex/volume-4/volume-4.pdf ./volume-4-distributed-systems.pdf

volume-5:
	@echo "==> Compiling volume-5-architecture-finops.pdf..."
	cd latex/volume-5 && pdflatex -interaction=nonstopmode volume-5.tex && pdflatex -interaction=nonstopmode volume-5.tex
	cp latex/volume-5/volume-5.pdf ./volume-5-architecture-finops.pdf

master:
	@echo "==> Compiling master-textbook.pdf..."
	cd latex/master && pdflatex -interaction=nonstopmode master-textbook.tex && pdflatex -interaction=nonstopmode master-textbook.tex
	cp latex/master/master-textbook.pdf ./master-textbook.pdf

clean:
	rm -f latex/*/*.aux latex/*/*.log latex/*/*.out latex/*/*.toc
