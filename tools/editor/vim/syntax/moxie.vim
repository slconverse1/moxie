" Vim syntax file for Moxie (.mxi).  Install: see README.md in this folder.
if exists("b:current_syntax")
  finish
endif

syn keyword moxieControl if elif else when while for in is return break continue yield go try_go do then select seq assert match
syn keyword moxieOperator and or not as where with using lazy update
syn keyword moxieDecl fn fiber tuple enum interface impl unit type test
syn keyword moxieModifier export internal priv static forward inline pure impure prints parks tailrec unsafe dynamic foreign pattern union opaque mutable move ref daemon deriving requires ensures invariant closes delegate property proxy forall import step todo handle any sql
syn keyword moxieConstant true false self Self
syn keyword moxieBuiltinType Int Int8 Int16 Int32 Int64 UInt UInt8 UInt16 UInt32 UInt64 BigInt Byte Double Float Decimal String Bool Char Unit Duration List Array Ring Set Dict Option Result Error Stream Chan ChanR ChanW Future FutureR FutureW Atom Range Secret
syn match   moxieType      "\<[A-Z][A-Za-z0-9_]*\>"
syn match   moxieWildcard  "\<_\>"
syn match   moxieCall      "\<[a-z_][A-Za-z0-9_]*\ze("
syn match   moxieNumber    "\<0[xX][0-9A-Fa-f_]\+\([iu]\(8\|16\|32\|64\)\)\=\>"
syn match   moxieNumber    "\<0[bB][01_]\+\([iu]\(8\|16\|32\|64\)\)\=\>"
syn match   moxieNumber    "\<[0-9][0-9_]*\.[0-9][0-9_]*\([eE][+-]\=[0-9]\+\)\=f\=\>"
syn match   moxieNumber    "\<[0-9][0-9_]*\([iu]\(8\|16\|32\|64\)\)\=\>"
syn match   moxieDuration  "\(\<[0-9][0-9_.]*\)\@<=\(ns\|us\|ms\|s\|m\|h\|d\)\>"
syn match   moxieArrow     "->\|\~>\|<\~"
syn match   moxiePipe      "|>>\|<\$>\|<\*>\||>"
syn match   moxieSpread    "\.\.\.\|\.\.<\|\.\."
syn match   moxieEscape    contained "\\."
syn region  moxieInterp    contained matchgroup=moxieDelim start="\${" end="}" contains=TOP
syn match   moxieInterpVar contained "\$[A-Za-z_][A-Za-z0-9_]*"
syn region  moxieString    start=+"""+ end=+"""+ contains=moxieEscape,moxieInterp,moxieInterpVar
syn region  moxieString    start=+"+ skip=+\\.+ end=+"+ oneline contains=moxieEscape,moxieInterp,moxieInterpVar
syn match   moxieChar      "'\(\\.\|[^'\\]\)'"
syn region  moxieComment   start="/\*" end="\*/" contains=moxieComment,moxieTodo
syn match   moxieComment   "//.*$" contains=moxieTodo
syn match   moxieDoc       "///.*$"
syn keyword moxieTodo      contained TODO FIXME XXX

hi def link moxieControl     Conditional
hi def link moxieOperator    Operator
hi def link moxieDecl        Keyword
hi def link moxieModifier    StorageClass
hi def link moxieConstant    Constant
hi def link moxieBuiltinType Type
hi def link moxieType        Type
hi def link moxieWildcard    Special
hi def link moxieCall        Function
hi def link moxieNumber      Number
hi def link moxieDuration    Number
hi def link moxieArrow       Operator
hi def link moxiePipe        Operator
hi def link moxieSpread      Operator
hi def link moxieEscape      SpecialChar
hi def link moxieInterpVar   Identifier
hi def link moxieDelim       Delimiter
hi def link moxieString      String
hi def link moxieChar        Character
hi def link moxieComment     Comment
hi def link moxieDoc         SpecialComment
hi def link moxieTodo        Todo

let b:current_syntax = "moxie"
