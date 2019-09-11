# call-explorer

Language agnostic path finding between source and target function calls.

## Supported languages

- Java
- C/C++ (via LLVM optimizer output in [dot format](https://en.wikipedia.org/wiki/DOT_(graph_description_language)))

## Requirements

- Java 1.8
- Python 2.7

Add environment variables:

```bash
export JAVA_HOME=/c/Program\ Files/Java/jdk1.8.0_141
export PATH=$PATH:$JAVA_HOME/bin
```

Install python dependencies:

```bash
pip install -r requirements.txt
# or
python2 -m pip install -r requirements.txt
```

## Usage

Some languages have dedicated helper scripts available:

### Java

Add your ears with the following convention:

- `./modules/NAME/NAME.ear`

Run shell scripts in the following order:

```bash
# Generates calls.txt using `java-callgraph`
./extract-calls.sh 

# Optional, generates source methods from wsdl files
./extract-methods.sh 

# Runs the python script from one source module against multiple target modules
./extract-summaries.sh $app $prefix
```

### C/C++

[Create CFG](https://gist.github.com/mudongliang/e911a9528bd61a6083e8692520a924a2):

```bash
clang -emit-llvm -c foo.c
opt -dot-cfg foo.bc
dot -Tpng -o foo.png foo.dot
```

**TODO**

### Other languages

**TODO**
