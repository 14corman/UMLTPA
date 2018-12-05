# Python Based Ad-block Parser

This is a parser for interpreting Adblock Plus [filter](https://easylist-downloads.adblockplus.org/easylist.txt) rules. It matches a string aginst the set of 14,000+ filters listed in easylist.txt. 

## Installation

Just fork the project and run parser.py in a Python interpreter.
Before you can test strings, instantiate the look up class:

`lookup = lookup()`

## Usage

To check whether a URL is blocked, run the following

`lookup.match_url(url)`

To check whether an element is blocked, run the following

`lookup.match_elem(elem)`

If you wish to insert your own filters, feel free to add them to easylist.txt.

## Performance

Checking whether an item is blocked is always O(1). When the lookup class is instantiated, it creates a dictionary based on substrings of length 8 from each item in the easylist. Only when the element or url entered has a match in the dictionary, will it check it against the corresponding regex rule. 

As a result, it is more efficient than other easylist parsers, which mostly compile and check against regex at run time. 

## Contributing

Souce code: [https://github.com/winkerxiao/adblock-parser](https://github.com/winkerxiao/adblock-parser)

Feel free to fork and take a look. Would love to get some feedback.
