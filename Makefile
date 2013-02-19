.PHONY: clean test tests

clean:
	find . -name '*.pyc' -delete

test: tests
tests:
	testify tests --summary
