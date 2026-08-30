+++
title = "JavaScript String Offsets and Unicode Surrogate Pairs"
date = 2020-05-31T00:00:00Z
draft = false
description = "Why JavaScript string offsets can disagree with other systems when text contains Unicode surrogate pairs—and how to handle it."

[social]
image = "social.webp"
image_alt = "Archive cover for JavaScript String Offsets and Unicode Surrogate Pairs."

[share]
disable = false
languages = ["en"]

[original_publication]
site = "LightTag.io"
path = "/blog/unicode-surrogate-pairs/"
+++
You'd think that getting a cursor position in text is a solved problem, but here are some surprising bugs:
>
> * In Windows PowerShell [pressing backspace doesn't work as you'd expect][2]
> * Jupyter Notebook had [misaligned cursor data until 2017][3]
> * DraftJS has [users occasionally baffled][4] because of incorrect text range data

If you and your users are having strange problems with user interaction on text that contains Unicode, you are not alone.
GitHub shows [1.1 million open][1] issues for *Surrogate Pairs* (the problem we're facing). Of those, 900 thousand
are TypeScript/JavaScript issues. If you got here on a Google search you are probably in the right place and in good company.

We recently faced this issue ourselves and in this post will share our understanding of the problem and how we handled it.

## Why Is This Happening?

JavaScript has this funny feature where some characters have a length 2.

```js
//js
'💩'length
> 2
```

This doesn't happen in every language

```python
//python3
len('💩')
>1
```

```bash
//bash
echo "💩" |wc
> 1       1       5
```

In fact, it even happens in the browser, here double-click this pile of poo 💩 and you'll see the browser select the poo and the preceding space.

Mathias Bynens explained the problem in his 2013 post, [JavaScript Has a Unicode Problem][5]. As a quick refresher,
JavaScript uses UTF-16 (everything else uses UTF8). In UTF16 most of the  characters you are used to are represented by 16 bits
which allows for 65,536 characters. Unicode  allows for over a million different characters, which UTF16 represents
as "surrogate pairs", of 16 bit units.

The thing that causes us pain, is that when we call *'💩'.length* JS will count the number of 16-bit points as opposed to the
number of characters.

The rest of the universe, except Java and Windows use UTF-8. UTF-8 is also a "variable length encoding", but the first point
for any character says how many points in total represent it, which makes it easy for the underlying system to give us back the
"true character length". That's why in Python3 *len('💩')* is 1.

Fun fact, in Python2.x where strings were not UTf8  we get *len('💩')==4*, the total number of bytes

```python
Python 2.7.17 (default, Apr 15 2020, 17:20:14)
[GCC 7.5.0] on linux2
Type "help", "copyright", "credits" or "license" for more information.
> > len('💩')
4
```

## Where Does It Hurt

This issue causes pain in two places when dealing with string offsets. When adjusting strings or cursor locations
based on an offset and when storing and retrieving offset data from a system that considers the length of '💩' to be 1.
Quoting from Bynens' article:
> This behavior leads to many issues. Twitter, for example, allows 140 characters per tweet, and their back-end doesn’t
>mind what kind of symbol it is — astral or not. But because the JavaScript counter on their website at some point
>simply read out the string’s length without accounting for surrogate pairs, it wasn’t possible to enter more than 70 astral symbols.
>(The bug has since been fixed.)

At LightTag we recently encountered this bug. When a user annotates text that was preceded by an astral code point (one that is
represented by a surrogate pair) we adjusted its offsets before saving on the server. We also have a review mode, where project
managers can see and correct what other annotators have done. The team originally missed adjusting server offsets into their JS
equivalents resulting in miss-displayed annotations.

## The Solution

It's easier to describe the solution with a bit of terminology.
Let's call any context that says  len('💩')=1 as P1 (Poo 1) and any context that says "💩".length =2 as P2.

We need to solve for moving from a P1 context to a P2 context and vice versa.
Moving from a P1 to a P2 means counting how many astral points appeared before a given offset and adding that number to the offset.
Going from a P2 to a P1 is similar, but we subtract instead of add.

The Jupyter Notebook repo has a nice example

```js
    function p2_idx_to_p1_idx (p2_idx, text) {
        var p1_idx = p2_idx;
        for (var i = 0; i < text.length && i < p2_idx; i++) {
            var char_code = text.charCodeAt(i);
            // check for the first half of a surrogate pair
            if (char_code >= 0xD800 && char_code < 0xDC00) {
                p1_idx -= 1;
            }
        }
        return p1_idx;
    }

    function p1_idx_to_p2_idx (p1_idx, text) {
        var p2_idx = p1_idx;
        for (var i = 0; i < text.length && i < js_idx; i++) {
            var char_code = text.charCodeAt(i);
            // check for the first half of a surrogate pair
            if (char_code >= 0xD800 && char_code < 0xDC00) {
                p2_idx += 1;
            }
        }
        return p2_idx;
    }

```

### References

[1]: https://github.com/search?q=%22surrogate+pairs%22&type=Issues
[2]: https://github.com/PowerShell/PowerShell/issues/12593
[3]: https://github.com/jupyter/jupyter_client/issues/259
[4]: https://github.com/facebook/draft-js/issues/2061
[5]:  https://mathiasbynens.be/notes/javascript-unicode
>
> 1. [GitHub Issue Search for Surrogate Pairs][1]
> 2. [Windows PowerShell Surrogate Pairs bug][2]
> 3. [JavaScript Has a Unicode Problem][5]
