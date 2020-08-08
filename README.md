# call-explorer

Language agnostic path finding between source and target function calls.

## Use Cases

- For legacy codebases, it is not clear how public-facing API methods are internally used. By traversing multiple methods at a time (vs. one at a time in an IDE), we get a faster understanding of their usage:
    - API methods that were deprecated (no calls target them);
    - Which controllers ([MVC pattern](https://en.wikipedia.org/wiki/Model%E2%80%93view%E2%80%93controller)) handle which API methods;
    - How some classes (e.g. utils) cover more API method implementations than others, which may involve higher refactoring costs.

## Example

The following steps use the ["Weather" sample](https://github.com/spring-projects/spring-ws-samples/tree/master/weather) from the Java Spring framework.

Retrieve the sample:

```bash
git submodule update --init --recursive
```

Consider the following method implementation:

```java
public class WeatherClient extends WebServiceGatewaySupport {

	public GetCityForecastByZIPResponse getCityForecastByZip(String zipCode) {

		GetCityForecastByZIP request = new GetCityForecastByZIP();
		request.setZIP(zipCode);

		System.out.println();
		System.out.println("Requesting forecast for " + zipCode);

		GetCityForecastByZIPResponse response = (GetCityForecastByZIPResponse) getWebServiceTemplate()
				.marshalSendAndReceive(request, new SoapActionCallback("http://ws.cdyne.com/WeatherWS/GetCityForecastByZIP"));

		return response;
	}

    // ...
}
```

We see a call to `setZIP`. Let's find all calls to it under the class `WeatherClient`:

```bash
./parsers/sum.py examples/data/calls.json <(echo 'weather') <(echo 'setZIP')
```

Output:

````markdown
# Calls

### 1
```
WeatherClient:main(String[])
WeatherClient:getCityForecastByZip(String)
    setZIP
```

# Total
```
setZIP:1
```
````

All patterns are case insensitive. Matches are done against classes or methods containing the substrings we provided.

Our script found the longest call path that reached the source method `getCityForecastByZip()`, starting at `main()`. All indented lines are of target methods reached from function `getCityForecastByZip()`. In this case, only one method contains the substring `setZIP`.

We can also confirm that the call to `marshalSendAndReceive` is done from an instance returned by a getter called in `getCityForecastByZip()`, so the path starts at that instance:

```bash
./parsers/sum.py examples/data/calls.json <(echo '') <(echo 'marshal')
```

Output:

````markdown
# Calls

### 1
```
WeatherConfiguration:weatherClient(Jaxb2Marshaller)
    setMarshaller
    setUnmarshaller
```

### 2
```
WeatherConfiguration:marshaller()
    setContextPath
```

### 3
```
WebServiceTemplate:marshalSendAndReceive(Object)
    marshalSendAndReceive
```

### 4
```
WebServiceTemplate:marshalSendAndReceive(String, Object)
    marshalSendAndReceive
```

# Total
```
setContextPath:1
setMarshaller:1
setUnmarshaller:1
marshalSendAndReceive:2
```
````

By design, the graph traversal algorithm only considers path expansion until the source class/method matches. This is why we don't see calls starting from `marshalSendAndReceive()`, so we would have to do additional queries to find them:

```bash
./parsers/sum.py examples/data/calls.json <(echo '') <(echo 'send')
```

Output:

````markdown
### 241
```
WebServiceTemplate:marshalSendAndReceive(String, Object)
WebServiceTemplate:marshalSendAndReceive(String, Object, WebServiceMessageCallback)
WebServiceTemplate:sendAndReceive(String, WebServiceMessageCallback, WebServiceMessageExtractor)
WebServiceTemplate:doSendAndReceive(MessageContext, WebServiceConnection, WebServiceMessageCallback, WebServiceMessageExtractor)
WebServiceTemplate:sendRequest(WebServiceConnection, WebServiceMessage)
    send
```
````

## Supported languages

- Java
- C/C++ (via LLVM optimizer output in [dot format](https://en.wikipedia.org/wiki/DOT_(graph_description_language)))

## Requirements

- Java 1.8 (Java parser)
- Python 2.7

Add environment variables:

```bash
export JAVA_HOME=/c/Program\ Files/Java/jdk1.8.0_141
export PATH=$PATH:$JAVA_HOME/bin
```

Install python dependencies:

```bash
pip2 install -r requirements.txt
# or
python2 -m pip install -r requirements.txt
```

## Usage

Some languages have dedicated helper scripts available:

### Java

#### 1. Parse classes from container

If you have all your dependencies in a container file format (e.g. `ear` or `war`), copy them under one of the following filesystem paths:

- `./$target_path/$name/$name.ear`
- `./$target_path/$name/$name.war`

And parse them:

```bash
# Generates calls.txt using `java-callgraph`
./extract-calls.sh 

# [OPTIONAL]: Generates source methods from wsdl files
./extract-methods.sh 
```

Otherwise, if you don't want to generate a "fat jar / uber jar / [shaded jar](https://maven.apache.org/plugins/maven-shade-plugin/) / [maven assembly's jar-with-dependencies](https://maven.apache.org/plugins/maven-assembly-plugin/descriptor-refs.html)", the simplest way is to copy all dependencies to a directory:

```bash
output_dir=
project_dir=

cd $project_dir
mvn dependency:copy-dependencies -DoutputDirectory="$(realpath "$output_dir")"
mvn package
cp target/*.jar "$output_dir"
```

Then parse all dependencies under that directory:

```bash
# Generates calls.txt using `java-callgraph`
./extract-calls-in-dir.sh "$output_dir"
```

#### 2. Convert calls from language-specific format to common format

```bash
./parsers/java-callgraph/parser.py <(echo examples/data/calls.txt) > examples/data/calls.json
```

#### 3. Summarize found paths

```bash
./parsers/sum.py examples/data/calls.json <(echo 'weather') <(echo 'setZIP')
```

Alternatively, to find paths across multiple projects:

```bash
# From source module `app` against multiple target modules, defined in script
./extract-summaries.sh $app
```

### C/C++

Create CFG:

```bash
clang -emit-llvm -c foo.c
opt -dot-cfg foo.bc
```

**TODO**
