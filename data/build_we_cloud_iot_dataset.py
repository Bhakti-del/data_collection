import re
import csv
import unicodedata
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CORPUS = ROOT / "data" / "cleaned_papers"
OUTDIR = ROOT / "data"

FIELDS = ["subject_name", "raw_question_text", "topic_tag", "bloom_level",
          "original_marks", "part_a_years", "part_b_years"]

WEB_TECH_KEYWORDS = {
    "PHP_CONTROL_STRUCTURES": [
        "control structure", "if else", "if-else", "else if", "for loop", "foreach",
        "while loop", "do-while", "do while", "loop in php", "switch statement",
        "break and continue", "break;", "continue;", "iterative statement",
    ],
    "PHP_FUNCTIONS_AND_ARRAYS": [
        "function in php", "user defined function", "predefined function", "function in javascript",
        "parameter passing", "argument", "return value", "array in php", "arrays used in php",
        "string functions", "sorting the elements", "ascending order", "function overloading",
        "reverse a string", "length of the string", "prime number", "leap year",
        "php arrays", "associative array", "multidimensional array",
    ],
    "PHP_FILE_HANDLING": [
        "file handling", "file operation", "binary file", "text file", "readfile", "feof",
        "fopen", "directory", "directories in php", "listing directories", "reading and writing",
        "specified directory", "designated directory", "external entity reference",
    ],
    "PHP_FORMS_AND_VALIDATION": [
        "web form", "form data", "validate", "validation", "login form", "login page",
        "username, password", "user id and password", "form consisting", "html form",
        "read data from web", "creating a web application",
    ],
    "PHP_SESSIONS_AND_COOKIES": [
        "session in php", "php session", "session variable", "session_start", "cookie",
        "login and logout", "session tracking in php", "server side state",
    ],
    "PHP_LANGUAGE_BASICS": [
        "php syntax", "syntax of php", "symbol in php", "html inside php", "pitfall",
        "php script", "interpreter", "features of php", "advantages of php",
        "introduction to php", "escaping", "comments in php", "variable in php",
        "how php fits", "cdata", "pcdata", "scripting element",
    ],
    "MYSQL_PHP_CONNECTIVITY": [
        "mysql", "database connectivity in php", "connect to database", "connecting the mysql",
        "storage engine", "execution of queries", "sql query", "employee table",
        "login table", "number of rows", "database connection through jsp",
    ],
    "XML_DTD": [
        "dtd", "document type definition", "internal dtd", "external dtd", "entity reference",
    ],
    "XML_SCHEMA": [
        "xml schema", "xmlscheme", "xml schemas", "schema language", "validating xml",
        "xml namespace", "data types in xml", "schema for", "well form schema",
        "attributes in dtd",
    ],
    "XML_PARSERS_DOM_SAX": [
        "dom parser", "sax parser", "dom and sax", "xml parser", "parsing xml",
        "dom methods", "xml dom", "need of parsers", "parsers in java", "parser in xml",
    ],
    "XML_FUNDAMENTALS_AND_SYNTAX": [
        "what is xml", "define xml", "xml syntax", "structure rules", "xml tags",
        "flow control tag", "transformation tag", "core tag", "xml elements",
        "xml document", "xml file", "features of xml", "xml advantages",
        "xml definition", "design a layout using xml",
    ],
    "XHTML": [
        "xhtml", "css", "stylesheet", "webpage design using css",
    ],
    "JAVABEANS": [
        "javabean", "java bean", "beans in jsp", "java beans", "bean in jsp",
        "business logic from presentation",
    ],
    "JDBC_DATABASE_ACCESS": [
        "jdbc", "jdbc driver", "statement in jdbc", "types of statements", "database username",
    ],
    "SERVLET_SESSION_MANAGEMENT": [
        "session tracking in servlet", "session management", "sessions in servlet",
        "cookies in servlet", "enable and disable session", "multithreaded servlet",
        "single threaded",
    ],
    "SERVLET_HTTP_REQUEST_RESPONSE": [
        "http get", "http post", "get request", "post request", "request and response",
        "handling http", "http request", "invoke other web resource", "get and post",
    ],
    "SERVLET_LIFECYCLE_AND_API": [
        "life cycle of a servlet", "lifecycle of servlet", "servlet api", "servlet architecture",
        "servlet container", "servlet works", "advantages of servlets", "what is a servlet",
        "brief note on servlet", "http servlet", "generic servlet", "servlet program",
        "servlet technology", "multithreaded",
    ],
    "JSP_IMPLICIT_OBJECTS": [
        "implicit object", "pagecontext", "page implicit", "session object", "request object",
        "response object",
    ],
    "JSP_TAGS_AND_LIBRARIES": [
        "tag extension", "tag library", "jsp libraries", "jsp code snippet", "jsp snippets",
        "custom tag",
    ],
    "JSP_STRUCTURE_AND_DIRECTIVES": [
        "jsp page", "structure of jsp", "anatomy of jsp", "components of a jsp",
        "jsp directive", "page directive", "include directive", "jsp declaration",
        "jsp processing", "jsp technology", "jsp application", "jsp program",
        "jsp processing", "jsp element",
    ],
    "JAVASCRIPT_DOM_EVENTS": [
        "event handler", "events in java", "keyboard event", "dom methods", "document object model",
        "dom in javascript", "text color", "handling events", "event object",
    ],
    "JAVASCRIPT_CONTROL_STRUCTURES": [
        "control structures in java", "control structure in javascript", "loop in javascript",
        "sorting the given elements", "sorting the elements",
    ],
    "JAVASCRIPT_FUNCTIONS_AND_OBJECTS": [
        "function in javascript", "functions in java", "objects, methods", "objects and methods",
        "this keyword", "dot operator", "function overloading", "create a function",
        "how to define a function in javascript",
    ],
    "JAVASCRIPT_BASICS": [
        "what is javascript", "features of javascript", "features of java script",
        "operators in javascript", "operators and datatypes", "data types in javascript",
        "variables in javascript", "date object", "client side java",
        "server side java", "server side javascript",
    ],
    "AJAX": [
        "ajax", "asynchronous javascript",
    ],
    "CGI": [
        "common gateway interface", "cgi variable", "cgi program", "cgi process", "cgi vs servlet",
        "cgi working", "servlets over cgi", "web servers that support cgi",
    ],
    "CLIENT_VS_SERVER_SIDE": [
        "server side programming", "client side programming", "client side and server side",
        "difference between client", "client side versus server side",
    ],
    "WEB_DEPLOYMENT_AND_MVC": [
        "deploying a web application", "deployment of web", "mvc set up", "mvc setup",
        "frames in creation", "frames in html",
    ],
}

CLOUD_KEYWORDS = {
    "CLOUD_MIGRATION": [
        "migrating into a cloud", "migration into cloud", "migration in to a cloud",
        "seven-step model", "seven step model", "phases of cloud migration",
        "phases involved in migrating", "migration risks", "migrating into a cloud environment",
        "factors influenced to migration", "application migration",
    ],
    "SLA_MANAGEMENT": [
        "sla management", "service level agreement", "sla in cloud", "sla lifecycle",
        "life cycle of sla", "phases of sla", "production readiness",
        "assess the production readiness", "workflow engine",
    ],
    "CLOUD_PLATFORM_FRAMEWORKS": [
        "aneka", "reservoir", "comet cloud", "saga map reduce", "google app engine",
        "cloud computing framework", "appliance",
    ],
    "VENDOR_CLOUD_SERVICES": [
        "aws", "amazon elastic", "azure", "windows azure", "smartcloud", "salesforce",
        "eucalyptus", "sap hana", "vmware", "captiva", "t-systems", "amazon web service",
        "amazon ec2",
    ],
    "CLOUD_INTEGRATION": [
        "integration as a service", "integration as a service paradigm", "cloud integration",
        "integration scenarios", "data integration engineering lifecycle", "cloud supply chain",
        "enriching the integration", "cloud contract",
    ],
    "CLOUD_CHANGE_MANAGEMENT": [
        "change management", "crops", "lewin", "cmmm", "change management maturity",
        "organization and structure",
    ],
    "CLOUD_DATA_SECURITY": [
        "data security", "security in cloud", "secure distributed data storage",
        "vulnerabilities in current cloud", "network threat", "data integrity",
        "external threat", "internal threat", "security is provided", "vulnerabilities",
    ],
    "CLOUD_IDENTITY_CONTENT_SECURITY": [
        "licensing agreement", "identity system", "user centric", "open identity",
        "content level security", "content-level security",
    ],
    "CLOUD_BUSINESS_LEGAL_ISSUES": [
        "business benefit", "legal issue", "commercial and business", "outsourcing",
        "provision of application service", "cloud user perspective", "pros and cons of cloud",
        "suitability", "motivation of cloud", "basic requirements for cloud service",
        "five essential characteristics", "characteristics of cloud",
    ],
    "CLOUD_MANAGEMENT": [
        "managing the cloud", "cloud management", "deming cycle", "management of virtual machine",
        "distributed management of virtual machine", "managing a cloud", "management in cloud",
    ],
    "CLOUD_NETWORKING": [
        "network connectivity", "applications in cloud", "network issue", "transport layer",
        "data center network",
    ],
    "VIRTUALIZATION_CLUSTERS_DATACENTERS": [
        "virtualization of cluster", "virtualization of data center", "virtualization of datacenter",
        "storage virtualization", "virtual cluster", "physical versus virtual cluster",
        "virtualize the server", "clusters and datacenters", "virtualization of clusters",
    ],
    "VIRTUAL_MACHINES": [
        "virtual machine", "primitive operation in virtual machine", "vm within opennebula",
        "live migration", "image management model", "virtual machine provisioning",
        "vm provisioning", "virtual machine migration", "virtual machine data model",
        "purpose of virtual machines", "features of virtual machine",
    ],
    "VIRTUALIZATION_CONCEPTS": [
        "what is virtualization", "concept of virtualization", "hardware virtualization",
        "hypervisor", "levels of virtualization", "virtualization structure",
        "virtualization tools", "implementation levels of virtualization",
        "virtualization service", "middle ware support for virtualization",
        "middleware support for virtualization", "virtualization infrastructure",
    ],
    "COMPUTER_CLUSTERS": [
        "computer cluster", "cluster architecture", "cluster computing", "design objectives of computer cluster",
        "cluster design issue", "scalable parallel computing", "computational grid",
        "cluster as a service", "caas", "cluster is used", "basic cluster",
    ],
    "HIGH_PERFORMANCE_COMPUTING": [
        "high performance computing", "high-performance computing", "hpc", "performance prediction",
        "degrees of parallelism", "performance metric", "performance of the metacdn",
    ],
    "PARALLEL_DISTRIBUTED_COMPUTING": [
        "parallel computing", "distributed computing", "distributed system",
        "distributed system model", "enabling technology", "distributed programming model",
        "physical versus virtual", "virtual clusters and resource",
    ],
    "CLOUD_ARCHITECTURE_ANATOMY": [
        "anatomy of the cloud", "architecture of federated", "federated cloud", "federation cloud",
        "metacdn", "layered architecture", "architecture of cloud", "architecture for cloud",
        "cloud architecture", "best practices in architecting", "best practices to build",
        "cloud application architecture",
    ],
    "CLOUD_SERVICE_MODELS": [
        "service model", "saas", "iaas", "paas", "software-as-a-service",
        "infrastructure as a service", "platform as a service", "spi model",
        "service-platform-infrastructure", "cloud service lifecycle", "cloud service life cycle",
        "cloud service offering", "delivery of cloud service", "services of cloud computing",
        "services provided by", "deployment and delivery",
    ],
    "CLOUD_DEPLOYMENT_MODELS": [
        "deployment model", "public cloud", "private cloud", "hybrid cloud",
        "enterprise cloud", "enterprise cloud computing", "types of clouds",
        "cloud integration scenarios",
    ],
    "CLOUD_FUNDAMENTALS": [
        "what is cloud computing", "define cloud computing", "cloud landscape",
        "principles of cloud", "cloud as a platform", "perspective as a platform",
        "features of cloud computing", "need of cloud", "cloud computing environment",
        "cloud era", "paradigm used for cloud", "features of cloud computing",
        "challenges in cloud", "cloud computing is",
    ],
    "COMPUTING_PARADIGMS": [
        "computing paradigm", "mobile computing", "grid computing", "nano computing",
        "optical computing", "pervasive computing", "computing environment",
        "technologies used to achieve",
    ],
}

IOT_KEYWORDS = {
    "WAMP_PROTOCOL": ["wamp"],
    "DJANGO_WEB_FRAMEWORKS": [
        "django", "web application framework", "web server for iot", "python web application",
    ],
    "PYTHON_STANDARD_LIBRARIES": [
        "urllib", "smtplib", "xml lib", "http lib", "standard library",
    ],
    "CLOUD_PLATFORMS_FOR_IOT": [
        "amazon web services for iot", "azure iot hub", "amazon ec2", "cloud storage model",
        "xively",
    ],
    "RASPBERRY_PI_PROGRAMMING": [
        "led on/off", "blink", "linux flavor", "interfacing external gadget",
        "raspberry pi using switch", "code for led", "operating system in raspberry",
    ],
    "RASPBERRY_PI_HARDWARE": [
        "raspberry pi board", "components of raspberry", "raspberry pi interface",
        "interfaces are available with raspberry", "functions used in raspberry",
        "raspberry pi model",
    ],
    "PYTHON_JSON_XML": [
        "json", "encoding and decoding", "xml and", "explain the following",
    ],
    "PYTHON_DATA_STRUCTURES_FUNCTIONS": [
        "list in python", "operations in python", "function creation and definition",
        "data structure in python", "functions in python",
    ],
    "PYTHON_LANGUAGE_FEATURES": [
        "features of python", "type conversion in python", "pass control structure",
        "exception handling in python", "python language", "classes in python",
    ],
    "IOT_SYSTEMS_MANAGEMENT": [
        "netopeer", "snmp", "iot management", "systems management", "management is required",
    ],
    "SDN_NFV_FOR_IOT": [
        "network function virtualization", "nfv", "software defined network", "sdn",
        "difference between sdn",
    ],
    "IOT_PROTOCOLS": [
        "application layer protocol", "iot protocol", "communication protocol",
        "url and web protocol",
    ],
    "IOT_COMMUNICATION_APIS": [
        "communication api", "communication model", "apis in iot",
    ],
    "M2M_VS_IOT": [
        "m2m vs iot", "m2m versus iot", "m2m vs m2m", "m2m and iot",
        "m2m applications", "m2m architecture", "difference between m2m",
    ],
    "IOT_APPLICATIONS_SMART_IRRIGATION": [
        "smart irrigation", "smart agriculture", "agriculture iot", "home automation",
        "case study", "application of iot",
    ],
    "IOT_LEVELS_TEMPLATES": [
        "iot level", "deployment template", "domain-specific", "template",
    ],
    "IOT_ENABLING_TECHNOLOGIES": [
        "enabling technolog", "big data generated by iot", "scope of iot",
        "limitation of conventional",
    ],
    "IOT_PHYSICAL_LOGICAL_DESIGN": [
        "physical design", "logical design", "block diagram of iot", "functional block",
        "anatomy of iot", "physical device",
    ],
    "IOT_DEFINITION_CHARACTERISTICS": [
        "define iot", "what is iot", "characteristics of iot", "iot objects",
    ],
}

IOT_FUND_KEYWORDS = {
    "IOT_INTEROPERABILITY": ["interoperability"],
    "BIG_DATA_ANALYTICS_IOT": [
        "hadoop", "storm cluster", "mapreduce", "map reduce", "data analytics",
        "data visualization", "data visualization and its importance", "big data in iot",
    ],
    "ETSI_M2M_STANDARDIZATION": [
        "etsi", "m2m domain", "high-level capabilit", "m2m service layer standardization",
        "service layer standardization",
    ],
    "IOT_DATA_COLLECTION": [
        "data collection", "data acquiring", "data acquisition",
    ],
    "IOT_PROTOCOL_STACK_6LoWPAN": [
        "6lowpan", "transport layer", "link layer protocol", "link all the devices",
        "link the devices", "importance of communication protocol", "device to link",
    ],
    "IOT_COMMUNICATION_MODELS": [
        "request-response", "request response", "communication model", "communication api",
    ],
    "IOT_FUNCTIONAL_BLOCKS_DESIGN": [
        "functional block", "components and business model", "business model pattern",
        "components in iot", "block diagram of iot",
    ],
    "IOT_CASE_STUDIES_APPLICATIONS": [
        "home automation", "environment monitoring", "smart home", "smart city",
        "connected vehicle", "interconnected transport", "application of iot",
        "iot applications",
    ],
    "SENSORS_AND_ACTUATORS": [
        "sensor", "actuator", "physical world", "energy type",
    ],
    "ARDUINO_PROGRAMMING": [
        "arduino", "led and switch", "analog sensor", "interface a sensor",
        "integrate sensors",
    ],
    "RASPBERRY_PI_INTERFACES_PROGRAMMING": [
        "raspberry pi", "spi and i2c", "i2c", "popular commands", "blink an led",
        "distribution supported", "model of raspberry", "raspberry pi a and b",
    ],
    "PYTHON_FOR_IOT": [
        "control structure in python", "python packages", "packages of interest for iot",
    ],
    "EMBEDDED_COMPUTING": ["embedded computing"],
    "CLOUD_FOR_IOT": [
        "cloud service model", "cloud platform for iot", "cloud computing",
        "advantages of cloud", "services of cloud",
    ],
    "SDN_FOR_IOT": ["sdn", "software defined network", "software-defined network"],
    "M2M_ARCHITECTURE_SERVICES": [
        "m2m system architecture", "architecture of m2m", "m2m high-level",
    ],
    "WIRELESS_COMMUNICATIONS_IOT": [
        "wireless communication", "network technologies", "link layer",
    ],
    "IOT_FUNDAMENTALS": [
        "main challenges", "challenges in internet of things", "characteristics of iot",
        "what is iot", "evolutionary phases", "information do internet",
        "what kind of information",
    ],
}

KEYWORD_ADDITIONS = {
    "WEB_TECH": {
        "PHP_LANGUAGE_BASICS": [
            "php", "reverse of any number", "multiple inheritance", "string operator",
            "data types supported by php", "casting of data types", "scope of variable",
            "declare variable", "declare array", "how strings are declared",
            "undefined and not defined", "comment", "constant", "operator in php",
            "operators used in php", "execution of queries", "execute a simple query",
            "query in php", "superclass", "object in php", "class in php", "oop in php",
            "operators in php", "print", "string concatenation",
        ],
        "PHP_CONTROL_STRUCTURES": [
            "break", "continue", "loop", "switch", "do-while", "do while", "for loop",
            "foreach", "while", "if statement", "else statement", "control flow",
        ],
        "PHP_FUNCTIONS_AND_ARRAYS": [
            "array", "function", "sort", "reverse", "string function", "substr",
            "strlen", "parameter", "argument", "return", "recursion",
        ],
        "PHP_SESSIONS_AND_COOKIES": [
            "session", "cookie", "logout", "login", "persistent",
        ],
        "PHP_FILE_HANDLING": [
            "file", "directory", "readfile", "binary", "read and write", "open and close",
            "storage", "upload", "download",
        ],
        "PHP_FORMS_AND_VALIDATION": [
            "form", "validate", "validation", "login", "user id", "username",
            "email field", "text field", "submit",
        ],
        "MYSQL_PHP_CONNECTIVITY": [
            "mysql", "database", "sql", "query", "table", "row", "jdbc",
            "statement", "connectivity", "storage engine",
        ],
        "XML_DTD": ["dtd", "document type definition", "entity"],
        "XML_SCHEMA": [
            "schema", "namespace", "validate", "transformation", "transform",
            "data type in xml", "xml schema",
        ],
        "XML_PARSERS_DOM_SAX": [
            "parser", "dom", "sax", "parse", "xml dom", "xml sax",
        ],
        "XML_FUNDAMENTALS_AND_SYNTAX": [
            "xml", "markup", "tag", "element", "attribute",
        ],
        "XHTML": ["xhtml", "css", "style", "webpage", "html document"],
        "JAVABEANS": ["bean", "javabean", "java bean"],
        "JDBC_DATABASE_ACCESS": ["jdbc", "driver", "statement", "result set", "connection"],
        "SERVLET_LIFECYCLE_AND_API": [
            "servlet", "life cycle", "lifecycle", "servlet api", "container",
            "thread", "web component", "init", "service method",
        ],
        "SERVLET_HTTP_REQUEST_RESPONSE": [
            "http", "request", "response", "get", "post", "header", "cookie header",
        ],
        "SERVLET_SESSION_MANAGEMENT": [
            "session tracking", "session management", "session in servlet",
            "cookie in servlet", "session", "persistent session", "multithread",
        ],
        "JSP_STRUCTURE_AND_DIRECTIVES": [
            "jsp", "directive", "page directive", "include directive", "declaration",
            "scriptlet", "jsp page", "action", "tag directive",
        ],
        "JSP_IMPLICIT_OBJECTS": [
            "implicit", "pagecontext", "session object", "request object",
            "response object", "out object", "config", "application object",
        ],
        "JSP_TAGS_AND_LIBRARIES": [
            "jsp tag", "tag library", "tag extension", "library", "custom tag",
            "action tag", "standard tag",
        ],
        "JAVASCRIPT_DOM_EVENTS": [
            "event", "dom", "document object", "handler", "onclick", "onload",
            "mouse", "keyboard", "text color", "innerhtml",
        ],
        "JAVASCRIPT_CONTROL_STRUCTURES": [
            "sorting", "sort", "array in javascript", "loop in javascript",
            "control structure in javascript", "sorting the given elements",
        ],
        "JAVASCRIPT_FUNCTIONS_AND_OBJECTS": [
            "object", "method", "property", "prototype", "closure", "array in java script",
            "how to create and use arrays", "function in javascript",
        ],
        "JAVASCRIPT_BASICS": [
            "javascript", "java script", "variable in java", "data type in java",
            "operator in java", "date", "this keyword", "scope of variables",
            "declare variables", "define event", "client side", "server side",
        ],
        "AJAX": ["ajax", "asynchronous", "xmlhttprequest"],
        "CGI": ["cgi", "gateway interface", "environment variable"],
        "CLIENT_VS_SERVER_SIDE": [
            "client side", "server side", "client-side", "server-side",
            "difference between client", "thick client", "thin client",
        ],
        "WEB_DEPLOYMENT_AND_MVC": [
            "deploy", "deployment", "mvc", "web application", "frame", "war file",
            "web.xml", "configure",
        ],
    },
    "CLOUD": {
        "CLOUD_FUNDAMENTALS": [
            "cloud", "cloud computing", "desired feature", "cloud landscape",
            "mashup", "composability", "scientific application", "cloud era",
            "basic requirement", "five essential characteristic", "need of cloud",
            "understanding scientific", "principle of cloud", "importance of setting up cloud",
        ],
        "COMPUTING_PARADIGMS": [
            "paradigm", "mobile computing", "grid", "nano", "optical", "pervasive",
            "ubiquitous", "computing environment",
        ],
        "CLOUD_DEPLOYMENT_MODELS": [
            "deployment model", "public cloud", "private cloud", "hybrid cloud",
            "enterprise cloud", "types of cloud", "federated", "federal",
            "multi cloud", "cloud scenario",
        ],
        "CLOUD_SERVICE_MODELS": [
            "saas", "iaas", "paas", "service model", "software as a service",
            "infrastructure as a service", "platform as a service", "spi model",
            "service lifecycle", "cloud computing service", "cloud service",
            "delivery of cloud", "cloud computing services", "service offering",
        ],
        "CLOUD_ARCHITECTURE_ANATOMY": [
            "anatomy of the cloud", "architecture", "layered architecture", "metacdn",
            "content delivery network", "cdn", "best practice", "architecture of federated",
            "aneka hybrid", "cloud architecture", "reference architecture",
        ],
        "VIRTUALIZATION_CONCEPTS": [
            "virtualization", "hypervisor", "virtual machine", "virtualized",
            "need of virtualization", "levels of virtualization", "virtualization concept",
            "hardware virtualization", "middleware support",
        ],
        "VIRTUAL_MACHINES": [
            "virtual machine", "vm", "opennebula", "migration", "provision",
            "image management", "virtual machine data model", "primitive operation",
            "management of virtual", "distributed management of virtual",
        ],
        "VIRTUALIZATION_CLUSTERS_DATACENTERS": [
            "virtualization of cluster", "virtualization of data center",
            "virtualization of datacenter", "storage virtualization", "virtual cluster",
            "physical versus virtual", "server virtualization", "datacenter",
            "virtualization and cluster",
        ],
        "COMPUTER_CLUSTERS": [
            "cluster", "computational grid", "caas", "scalable parallel",
            "design objective", "cluster as a service", "types of cluster",
            "cluster computing", "cluster architecture", "cluster design",
        ],
        "HIGH_PERFORMANCE_COMPUTING": [
            "hpc", "high performance", "high-performance", "performance prediction",
            "degrees of parallelism", "performance metric", "performance of the metacdn",
            "supercomputer",
        ],
        "PARALLEL_DISTRIBUTED_COMPUTING": [
            "parallel", "distributed system", "distributed computing", "enabling technolog",
            "distributed programming", "distributed management", "resource management",
        ],
        "CLOUD_MIGRATION": [
            "migration", "migrating", "seven-step", "seven step", "phase of cloud migration",
            "stage of cloud migration", "migration risk", "migration into",
        ],
        "CLOUD_INTEGRATION": [
            "integration", "cloud integration", "supply chain", "integration scenario",
            "mashup", "enriching the integration", "data integration",
        ],
        "CLOUD_PLATFORM_FRAMEWORKS": [
            "aneka", "reservoir", "comet cloud", "saga", "app engine",
            "open nebula", "opennebula", "workflow engine", "cloud framework",
            "appliance", "t-system",
        ],
        "VENDOR_CLOUD_SERVICES": [
            "aws", "amazon", "azure", "smartcloud", "salesforce", "eucalyptus",
            "sap", "vmware", "captiva", "t-system", "google", "oracle",
            "windows azure", "commercial cloud", "provider",
        ],
        "SLA_MANAGEMENT": [
            "sla", "service level agreement", "production readiness", "readiness",
            "organizational readiness", "self-assessment", "workflow engine",
            "sla management", "sla lifecycle", "life cycle of sla", "sla mangement",
        ],
        "CLOUD_CHANGE_MANAGEMENT": [
            "change management", "crops", "lewin", "cmmm", "maturity model",
            "cultural", "organization", "process, skills",
        ],
        "CLOUD_DATA_SECURITY": [
            "security", "data security", "secure", "vulnerabilit", "threat",
            "integrity", "encryption", "attack", "privacy", "confidentiality",
        ],
        "CLOUD_IDENTITY_CONTENT_SECURITY": [
            "identity", "licensing", "content level security", "content-level security",
            "user centric", "open identity", "authentication",
        ],
        "CLOUD_BUSINESS_LEGAL_ISSUES": [
            "business", "legal", "commercial", "outsourcing", "benefit", "advantage",
            "disadvantage", "pros and cons", "suitability", "motivation", "cost",
        ],
        "CLOUD_MANAGEMENT": [
            "managing", "management", "deming", "manage", "cloud management",
            "management in cloud", "governance",
        ],
        "CLOUD_NETWORKING": [
            "network", "connectivity", "transport layer", "data center network",
            "application in cloud", "bandwidth", "latency",
        ],
        "CLOUD_MASHUPS_AND_CDN": [
            "mashup", "content delivery network", "cdn", "composability",
            "resource cloud mashup", "cloud mashup",
        ],
    },
    "IOT": {
        "IOT_DEFINITION_CHARACTERISTICS": [
            "define iot", "what is iot", "characteristic of iot", "iot object",
            "scope of iot", "conventional network", "big data generated",
            "iot is", "internet of things",
        ],
        "IOT_PHYSICAL_LOGICAL_DESIGN": [
            "physical design", "logical design", "block diagram", "functional block",
            "physical device", "endpoint", "general block",
        ],
        "IOT_ENABLING_TECHNOLOGIES": [
            "enabling technolog", "big data generated by iot", "limitation of conventional",
            "scope of iot", "enabling technology",
        ],
        "IOT_LEVELS_TEMPLATES": [
            "iot level", "level-2", "level-6", "deployment template", "domain-specific",
            "template",
        ],
        "IOT_APPLICATIONS_SMART_IRRIGATION": [
            "smart irrigation", "agriculture", "home automation", "case study",
            "smart city", "environment monitoring", "iot application", "useful in smart",
        ],
        "M2M_VS_IOT": [
            "m2m", "machine to machine", "difference between m2m", "vs iot",
        ],
        "IOT_COMMUNICATION_APIS": [
            "communication api", "communication model", "api", "iot communication",
        ],
        "IOT_PROTOCOLS": [
            "protocol", "application layer", "restful", "url",
        ],
        "SDN_NFV_FOR_IOT": [
            "sdn", "nfv", "network function virtualization", "software defined network",
            "software-defined network",
        ],
        "IOT_SYSTEMS_MANAGEMENT": [
            "netopeer", "snmp", "management", "netconf", "yang",
        ],
        "PYTHON_LANGUAGE_FEATURES": [
            "python", "type conversion", "control structure", "exception handling",
            "feature of python", "class in python", "pass",
        ],
        "PYTHON_DATA_STRUCTURES_FUNCTIONS": [
            "list in python", "operation in python", "function creation",
            "data structure", "list",
        ],
        "PYTHON_JSON_XML": ["json", "xml", "encoding", "decoding"],
        "PYTHON_STANDARD_LIBRARIES": ["urllib", "smtplib", "xml lib", "http lib", "library"],
        "RASPBERRY_PI_HARDWARE": [
            "raspberry pi", "interface", "board", "component", "function",
        ],
        "RASPBERRY_PI_PROGRAMMING": [
            "led", "blink", "linux flavor", "interfacing", "code for", "switch",
            "operating system",
        ],
        "CLOUD_PLATFORMS_FOR_IOT": [
            "amazon web service", "amazon service", "azure", "iot hub", "amazon ec2",
            "xively", "cloud storage",
        ],
        "WAMP_PROTOCOL": ["wamp", "autobahn"],
        "DJANGO_WEB_FRAMEWORKS": [
            "django", "web application framework", "web server", "python web",
        ],
    },
    "IOT_FUND": {
        "IOT_FUNDAMENTALS": [
            "challenge", "characteristic of iot", "what is iot", "evolutionary phase",
            "information do internet", "kind of information", "iot is",
        ],
        "IOT_FUNCTIONAL_BLOCKS_DESIGN": [
            "functional block", "business model", "component", "block diagram", "iot block",
        ],
        "WIRELESS_COMMUNICATIONS_IOT": [
            "wireless communication", "network technolog", "link layer", "bluetooth",
            "zigbee", "wifi",
        ],
        "IOT_PROTOCOL_STACK_6LoWPAN": [
            "6lowpan", "transport layer", "link layer protocol", "link all the devices",
            "link the devices", "protocol", "coap", "application layer", "rpl",
            "communication protocol", "importance of communication",
        ],
        "IOT_COMMUNICATION_MODELS": [
            "request-response", "request response", "communication model", "api",
            "pub-sub", "publish subscribe",
        ],
        "M2M_ARCHITECTURE_SERVICES": [
            "m2m system architecture", "architecture of m2m", "m2m", "application of m2m",
            "service layer standardization", "m2m domain", "etsi",
        ],
        "ETSI_M2M_STANDARDIZATION": [
            "etsi", "m2m domain", "high-level capabilit", "standardization",
        ],
        "SENSORS_AND_ACTUATORS": [
            "sensor", "actuator", "physical world", "energy type", "interface a sensor",
            "led and switch", "switch",
        ],
        "EMBEDDED_COMPUTING": ["embedded computing", "embedded system", "embedded"],
        "ARDUINO_PROGRAMMING": [
            "arduino", "led", "switch", "analog sensor", "integrate sensor",
            "arduino programming", "arduino coding",
        ],
        "RASPBERRY_PI_INTERFACES_PROGRAMMING": [
            "raspberry pi", "spi", "i2c", "popular command", "blink an led",
            "distribution", "model of raspberry", "interface",
        ],
        "PYTHON_FOR_IOT": [
            "python", "control structure", "package", "packages of interest",
        ],
        "SDN_FOR_IOT": ["sdn", "software defined network", "sdn layer"],
        "CLOUD_FOR_IOT": [
            "cloud", "service model", "cloud platform", "advantage of cloud",
        ],
        "BIG_DATA_ANALYTICS_IOT": [
            "hadoop", "strom", "storm cluster", "mapreduce", "map reduce",
            "data analytics", "data visualization", "big data", "analytics",
        ],
        "IOT_INTEROPERABILITY": ["interoperability", "interoperable"],
        "IOT_DATA_COLLECTION": [
            "data collection", "data acquiring", "data acquisition", "collecting data",
        ],
        "IOT_CASE_STUDIES_APPLICATIONS": [
            "home automation", "environment monitoring", "smart home", "smart city",
            "connected vehicle", "interconnected transport", "application",
            "transport system",
        ],
    },
}

SEMANTIC_WEB_KEYWORDS = {
    "SEMANTIC_BIOINFORMATICS": [
        "bioinformatics",
    ],
    "E_LEARNING": [
        "e-learning", "elearning", "educational semantic web", "education",
    ],
    "UML_VISUAL_MODELING": [
        "uml", "visual modeling", "visual modelling",
    ],
    "SOCIAL_NETWORK_MINING": [
        "social network mining", "disambiguation", "person name",
        "social science", "ubiquitous device", "small device", "web based network",
        "sociological", "social phenomenon", "social phenomena", "technology adoption",
    ],
    "SOCIAL_NETWORK_METRICS": [
        "centrality", "jaccard", "referral chaining", "snowballing", "random graph",
        "network analysis", "personal network", "co-occurrence", "sociogram",
        "degree central", "global structure", "macro-structure",
    ],
    "ELECTRONIC_DISCUSSION_NETWORKS": [
        "electronic discussion", "discussion network", "discussion forum",
    ],
    "BLOGS_AND_ONLINE_COMMUNITIES": [
        "blog", "online communit", "flink", "weblog",
    ],
    "SOCIAL_NETWORK_ANALYSIS": [
        "social network", "social networks", "relational data", "relational table",
        "social analysis", "social network analysis",
    ],
    "SEMANTIC_SEARCH": [
        "semantic search", "latent semantic", "concept ranking", "relevancy",
        "search engine", "swoogle", "google search", "search algorithm",
        "web search", "semantic based search", "rank and relevancy", " tap",
        "information retrieval", "search operation",
    ],
    "SEMANTIC_WEB_SERVICES": [
        "semantic web service", "owl-s", "owl -s", "service profile",
        "soap", "web service", "service description", "process ontology",
        "next generation web service", "dynamically invoked", "goal template",
        "service and profile", "automated by owl", "semantic service",
        "expressive power", "service discovery",
    ],
    "SOFTWARE_AGENTS": [
        "software agent", "intelligent agent", "search agent", "adaptive software",
        "soft computing", "define software", "agent",
    ],
    "SEMANTIC_WEB_APPLICATIONS": [
        "semantic web application", "building semantic web", "architecture of semantic web application",
        "enterprise application integration", "sesame", "rdf data repository",
        "web application", "devise an application", "building web application",
    ],
    "KNOWLEDGE_BASES": [
        "knowledge base", "knowledge base system", "expert system",
        "different from database", "knowledge representation",
    ],
    "CHAINING_AND_REASONING": [
        "forward chaining", "backward chaining", "reasoning with semantic",
        "reasoning", "illustrate reasoning", "minimum necessary expressive power",
    ],
    "RULES_MONOTONIC_NONMONOTONIC": [
        "modus ponens", "modus tollens", "monotonic", "monotonic rules",
        "nonmonotonic", "non monotonic", "rules where information",
        "conflict", "rules are preferred",
    ],
    "INFERENCE_ENGINES": [
        "inference engine", "inference en gine", "rdfs inference",
        "rdf inference", "inference in detail", "working principle",
    ],
    "DESCRIPTION_LOGIC": [
        "descriptive logic", "description logic",
    ],
    "LOGIC_ON_SEMANTIC_WEB": [
        "logic on the semantic", "logic and inference", "logic, inference",
        "logic proof", "define inference", "what is inference", "logic behind",
    ],
    "ONTOLOGY_MAPPING_MERGING": [
        "sharing and merging", "ontology mapping", "ontology matching",
        "matching and mapping", "learning source description", "ontology merge",
    ],
    "ONTOLOGY_KNOWLEDGE_REPRESENTATION": [
        "knowledge representation", "spot", "multi -specialty", "multi specialty",
        "multi-specialty", "specialty hospital", "ontology-based",
    ],
    "ONTOLOGY_ENGINEERING_TOOLS": [
        "ontology engineering", "ontology development tool", "ontology library",
        "famous ontology", "constructing ontology", "building ontology",
        "sesame repository", "ontology libraries", "development tool",
        "ontology method", "approach for building ontology", "ontology tool",
        "ontology mapping and tool", "about ontology", "ontology schema",
    ],
    "OWL_ONTOLOGY_LANGUAGES": [
        "owl", "owl-dl", "owl-lite", "ontology language", "web ontology language",
        "ontology sub-language", "ontology sublanguages", "sub-languages",
        "essentials of an owl", "web ontology", "ontology example",
        "requirements of ontology", "ontology and owl",
    ],
    "RDF_SCHEMA_RDFS": [
        "rdf schema", "rdfs", "rdfs layer", "rdf/rdfs", "rdf and rdfs",
        "relationship with rdf schema", "describe rdf and rdf schema",
    ],
    "RDF_FUNDAMENTALS": [
        "rdf", "xquey", "reification", "elements of rdf", "properties of rdf",
        "inference in rdf", "resource description framework",
    ],
    "XML_HTML_COMPARISON": [
        "xml", "html", "xquey", "xml schema", "dtd file", "html language",
        "html document",
    ],
    "WEB_EVOLUTION_AND_REVOLUTIONS": [
        "information revolution", "industrial revolution", "agriculture revolution",
        "information age", "tim berner", "berners lee", "information revolution",
        "knowledge management",
    ],
    "SEMANTIC_WEB_FUNDAMENTALS": [
        "semantic web", "semantic web architecture", "world wide web", "the web",
        "next generation web", "road map", "roadmap", "limitations of today",
        "wrong with the web", "solvable on the web", "intelligent capabilities",
        "what is web", "define web", "web evolves", "goals of semantic",
        "objectives of semantic", "semantic web services", "overview on semantic",
        "semantic method",
    ],
    "AI_MACHINE_INTELLIGENCE": [
        "machine intelligence", "artificial intelligence", "machine learning",
        "intelligent device", "computational complexity", "expert system",
        "number of nodes on the web", "limit the ability",
    ],
}

ADV_ALGO_KEYWORDS = {
    # Declared before QUICK_SORT / HEAP_SORT so that "randomized quicksort"
    # and "randomized heap sort" resolve here rather than to the base sort.
    "RANDOMIZED_ALGORITHMS": [
        "randomized algorithm", "randomised algorithm",
        "randomized heap sort", "random sorting",
    ],
    "QUICK_SORT": [
        "quick sort", "quicksort", "partition", "pivot",
        "best-case time for quick", "worst-case time for quick",
        "best case analysis of quick", "worst case analysis of quick",
        "time complexity of quick sort",
    ],
    "HEAP_SORT": [
        "heap sort", "heapsort", "max-heap-insert", "heap-insert",
        "min heap", "max heap", "binary heap", "heap strategy",
    ],
    "ZERO_ONE_PRINCIPLE": [
        "zero-one principle", "zero one principle", "zero -one principle",
        "zero - one principle",
    ],
    "SORTING_NETWORKS": [
        "sorting network", "sorting networks", "bitonic", "bio tonic",
        "merging network", "merging networks", "comparison network",
        "comparision network", "comparison networks", "comparator between",
    ],
    "MATRIX_CHAIN_MULTIPLICATION": [
        "matrix chain", "matrix-chain", "chain matrix",
        "parenthesization", "parenthesisation", "optimal parenthes",
    ],
    "MATRIX_MULTIPLICATION_STRASSEN": [
        "strassen", "matrix multiplication",
    ],
    "MATRIX_INVERSION_LUP": [
        "inverse of", "inverting matrices", "matrix inversion",
        "lup-decomposition", "lup decomposition", "compute inverse",
        "find the inverse",
    ],
    "LINEAR_EQUATIONS_SOLVING": [
        "system of linear equations", "systems of linear equations",
        "linear equation", "linear equations", "solving system of linear",
        "solve the system of linear", "by substitution",
    ],
    "STRING_MATCHING_NAIVE": [
        "naive string", "naive algorithm", "naive string matcher",
        "brute force", "best case of naive", "navie bayes string",
        "naive bayes string",
    ],
    "STRING_MATCHING_KMP": [
        "knuth-morris-pratt", "knuth morris", "knuth morries",
        "knuth-morris", "kmp",
    ],
    "STRING_MATCHING_RABIN_KARP": [
        "rabin -karp", "rabin-karp", "rabin - karp", "rabin karp",
        "spurious hits", "module q",
    ],
    "FINITE_AUTOMATA_STRING_MATCHING": [
        "finite automata", "string-matching automat",
        "string matching automat", "matching of a string using finite",
        "deterministic and non deterministic",
    ],
    "STRING_MATCHING_FUNDAMENTALS": [
        "string matching", "pattern in string",
        "applications of string-matching",
    ],
    "HUFFMAN_CODING": [
        "huffman", "variable-length huffman",
    ],
    "SPANNING_TREE_PRIM": [
        "prim's", "prim’s", "prim algorithm",
    ],
    "SPANNING_TREE_KRUSKAL": [
        "kruskal", "minimum spanning tree", "minimum cost spanning tree",
        "min cost spanning tree",
    ],
    "SHORTEST_PATH_ALGORITHMS": [
        "single source shortest path", "shortest path",
        "floyd-warshall", "floyd warshall", "dijkstra",
    ],
    "MAXIMUM_FLOW": [
        "maximum flow", "max flow", "maxflow",
    ],
    "TOPOLOGICAL_SORTING": [
        "topological sort", "topological sorting",
        "directed acyclic graph",
    ],
    "DYNAMIC_PROGRAMMING": [
        "dynamic programming", "principle of optimality",
        "knapsack", "dp formulation",
    ],
    "OPTIMAL_BINARY_SEARCH_TREE": [
        "optimal binary search tree", "obst", "binary search tree",
    ],
    "LONGEST_COMMON_SUBSEQUENCE": [
        "longest common subsequence", "lcs",
    ],
    "ALGORITHM_ANALYSIS_FOUNDATIONS": [
        "recurrence", "recurrence equation", "substitution method",
        "recursion tree", "asymptotic bound", "amortized analysis",
        "amortised analysis", "role of algorithms in computing",
        "role of algorithms", "tight upper bound", "running time of",
    ],
    "RANDOMIZED_ALGORITHMS": [
        "randomized algorithm", "randomised algorithm",
        "randomized heap sort", "random sorting",
    ],
    "GREEDY_ALGORITHMS": [
        "greedy", "activity selection", "n jobs", "profit gi",
        "unit time", "not later than the time d",
    ],
    "NP_COMPLEXITY_CLASSES": [
        "np-complete", "np complete", "np-hard", "np hard",
        "polynomial time", "class p", "classes p", "p = np",
        "non-deterministic algorithm", "nondeterministic algorithm",
        "np-completeness", "p and np",
    ],
    "APPROXIMATION_ALGORITHMS": [
        "approximation algorithm", "approximation algorithms",
        "approx-vertex-cover", "approximation",
    ],
    "VERTEX_COVER_PROBLEM": [
        "vertex cover", "vertex-cover", "vertex cover problem",
        "professor nixon",
    ],
    "TRAVELLING_SALESMAN_PROBLEM": [
        "travelling salesman", "traveling salesman", "travelling sales",
        "traveling sales", "tsp",
    ],
}

# Questions that cannot be answered because the required figure/graph was never
# rendered into the cleaned text. Matched against the cleaned question text.
ADV_ALGO_EXCLUDE = [
    re.compile(r"max flow of the following graph", re.I),
    re.compile(r"as shown in figure\s*1", re.I),
    re.compile(r"below figure\s*2", re.I),
    re.compile(r"kruskal.{0,25}algorithm for the given graph", re.I),
    re.compile(r"implement for the following graph", re.I),
    re.compile(r"following instance of the single source", re.I),
]

SCRIPTING_KEYWORDS = {
    # ---------- general scripting ----------
    "SCRIPTING_LANGUAGE_FOUNDATIONS": [
        "need of scripting", "characteristics of scripting",
        "applications of scripting", "modern scripting", "uses of scripting",
        "three different meanings of scripting", "origin of scripting",
        "visual scripting", "compare scripting languages",
        "scripting languages and compare", "what is scripting",
        "scripting language", "traditional scripting", "features of scripting",
        "tcl, tk and perl", "python and php", "over other programming languages",
        "features of php", "features of python", "advantages of python",
        "most preferred language", "advantage of php", "features and fundamental concepts of tk",
    ],
    "WEB_SCRIPTING_AND_FORMS": [
        "web scripting", "web application", "web system", "cgi script",
        "internet ware application", "internet-aware application",
        "web server architecture", "web form", "html entities", "web forms", "web sites for the world",
        "embed php code", "output the data to a browser",
        "output the data to browser", "html_quickform2", "validate a simple form",
        "create and validate", "pass data from a web form",
        "increase the user experience", "php and web forms",
    ],
    # ---------- Perl ----------
    "PERL_DATA_TYPES_VARIABLES": [
        "rules for naming variables", "data types that perl can handle",
        "scalar data, numeric constants", "string constants",
        "perl data types", "list the data types", "prefix dereferencer",
        "reserved word", "dispense with variable declarations",
        "names and values in perl", "arguments that are used frequently in perl",
    ],
    "PERL_ARRAYS_HASHES": [
        "arrays and hashes", "lists with hashes", "lists and hashes",
        "arrays in perl", "hash of arrays", "array of hashes", "array of arrays",
        "push and pop in array", "size of hash", "define hashes in perl",
        "how to create and implement hashes", "define hash",
        "variables and data structures", "data structures used in perl",
    ],
    "PERL_REFERENCES_SUBROUTINES": [
        "subroutines in perl", "define and call a subroutine", "subroutine to find",
        "subroutine that calculates", "code reusability", "constructor",
        "subroutine in perl", "perl one-liner",
    ],
    "PERL_SCOPE_REFERENCES": [
        "create and use references in perl", "references to arrays",
        "closure concept in perl", "references and subroutines",
        "references in perl",
    ],
    "PERL_CONTROL_FLOW": [
        "control statements of perl", "control statements available in perl",
        "loops and decision making statements available in perl",
        "while and until", "next and last", "last and next",
        "perl for loop iterate", "control flow statements of perl",
        "control structures in detail",
    ],
    "PERL_OPERATORS_EXPRESSIONS": [
        "operators available in perl", "built-in operators and pattern",
        "logical operators", "scalar expressions", "expressions in php",
    ],
    "PERL_FILE_IO": [
        "files and data in perl", "file status check", "file system operations in perl",
        "seek, split and join", "pack function of perl", "pack( ) and unpack", "pack and unpack",
        "pack and upack", "tied variables", "fetch, store methods",
        "associate a stream with a file", "file handling i/o functions",
        "sysread and syswrite", "navigating the file system using perl",
        "gmtime()", "file handling",
    ],
    "PERL_REGULAR_EXPRESSIONS": [
        "regular expressions in perl", "pattern and regular expressions",
        "regular expressions and pattern matching", "pattern matching operators available",
        "grep function in perl", "rich form of regular expressions",
        "support provided by perl for regular expressions",
        "substitution operators in perl", "regular expressions", "regexp",
    ],
    "PERL_MODULES_PACKAGES": [
        "packages and modules in perl", "create packages and modules",
        "typeglob", "modules and objects in perl", "create package in perl",
        "modules, objects in perl", "define a module and a package",
        "module and a package",
    ],
    "PERL_DEBUGGING_INTERPRETER": [
        "perl debugger", "debugging is done in perl", "debugging in perl",
        "running and debugging perl", "arguments for perl interpreter",
        "perl interpreter",
    ],
    "PERL_SECURITY": [
        "security issues in perl", "approach to provide security",
        "security issues in internet programming",
    ],
    "PERL_OS_INTERNET_INTERFACING": [
        "interface to operating system in perl", "interfacing to an operating system",
        "internet applications using perl", "perl interfacing",
    ],
    "PERL_TOOLKITS": [
        "purpose of perl-tk", "perl toolkits",
    ],
    # ---------- PHP ----------
    "PHP_BASICS": [
        "define php", "rules to construct a variable in php",
        "how to create functions in php", "function libraries in php",
        "type identifier functions", "string interpolation",
    ],
    "PHP_DATATYPES_EXPRESSIONS": [
        "data types available in php", "expressions in php",
        "scalar expressions", "php datatypes", "different types of assignment statements of php",
        "concatenation- assignment", "different meanings of scripting",
    ],
    "PHP_CONTROL_STRUCTURES": [
        "control structures in php", "php control structure",
        "short-circuit syntax", "short circuit syntax",
        "for and foreach statements", "for ii) foreach", "while iv) do-while",
    ],
    "PHP_EMBEDDING_AND_OUTPUT": [
        "embed php code into the web pages", "embedded php code in your web pages",
        "illustrate how php code is embedded", "process to embed php code",
        "output the data to a browser", "output the data to browser",
    ],
    "PHP_EMAIL_AND_UPLOAD": [
        "sending email using php", "steps for sending email",
        "procedure for sending email", "uploading files with php",
        "file-upload", "file upload functions",
    ],
    "PHP_AUTHENTICATION_LOGIN": [
        "authentication", "login administration", "one-time urls",
        "password recovery", "http protocol",
    ],
    "PHP_ENCRYPTION_SECURITY": [
        "mcrypt", "encryption functions", "security vulnerability of php",
        "cross -site scripting", "cross-site scripting", "cross site scripting",
        "data validation solutions", "security issues",
    ],
    "PHP_ECHO_PRINT": [
        "echo and print", "differentiate between echo and print",
    ],
    "PHP_DATABASE_ACCESS": [
        "mysql_connect", "mysql_pconnect", "cracklib",
    ],
    # ---------- Python ----------
    "PYTHON_DATA_TYPES": [
        "lists, tuples and dictionary", "lists tuples and dictionary",
        "intrinsic sequence types", "type and range functions",
        "sequence types of python", "data structures are supported by python",
        "how lists differ from tuples", "what is a list", "difference between a primary group",
        "set data structure", "classes? how they differ from dictionaries",
    ],
    "PYTHON_CONTROL_FLOW": [
        "control flow tools in python", "control flow in python",
        "while loop structures", "loop structures in python",
        "top-down and bottom-up approach in python",
    ],
    "PYTHON_FUNCTIONS": [
        "recursive functions in python", "functions in python",
        "methods in lists of python", "does function call create namespaces",
        "built-in functions and methods",
    ],
    "PYTHON_MODULES_LIBRARIES": [
        "create modules in python", "modules in python",
        "standard libraries in python", "standard library",
        "numpy package", "features of pandas", "sort a data frame",
    ],
    "PYTHON_EXCEPTION_HANDLING": [
        "exception handling in python", "handle the exception in python",
        "handle exceptions in python", "handle an exception using try",
        "how python handles exceptions", "user defined exception",
        "what is an exception", "error and exception",
        "benefits of exception handling", "exception handling",
    ],
    "PYTHON_TYPE_CASTING": [
        "type casting",
    ],
    "PYTHON_INTERPRETER": [
        "python interpreter", "difference between python and python scripting",
    ],
    "PYTHON_FILE_IO": [
        "modes in which a file can be opened", "command line arguments in python",
    ],
    "PYTHON_OBJECT_ORIENTED": [
        "operator overloading", "python class",
    ],
    "PYTHON_MEMORY_MANAGEMENT": [
        "memory managed in python",
    ],
    "PYTHON_STRING_FUNCTIONS": [
        "count number of characters", "compare echo and print statements in python",
    ],
    # ---------- Tcl ----------
    "TCL_LISTS": [
        "operations on tcl lists", "create a list in tcl", "list in tcl",
        "remove duplicates in the given list", "list data structure differs from an array",
        "operations performed on a list", "append command in tcl",
        "subroutine that calculates the sum of numbers in a list",
        "print fibonacci numbers",
    ],
    "TCL_CONTROL_FLOW": [
        "control flow commands of tcl", "control flow commands in tcl",
        "various control flow commands in tcl", "control structures in detail",
        "for and foreach statements in tcl",
    ],
    "TCL_VARIABLES_DATA_STRUCTURES": [
        "variables and data structures in tcl", "tcl data structures",
        "patterns available in tcl", "syntax for names and values",
        "length of a string without using", "puts and get commands",
    ],
    "TCL_EVAL_EXEC_SOURCE": [
        "uplevel command", "demonstrate uplevel", "illustrate uplevel",
        "eval, source, exec and uplevel", "eval function", "evel", "uses of sources in tcl",
        "global, upvar and uplevel", "global upvar and uplevel",
    ],
    "TCL_EVENTS": [
        "idle event", "event driven program in tcl",
    ],
    "TCL_SECURITY": [
        "security issues to be handled in tcl", "security issues in tcl",
    ],
    "TCL_INTERNET_PROGRAMMING": [
        "internet applications using tcl", "tcl internet programming",
        "tcl as an embedded system", "internet programming of tcl",
        "recursive procedures in tcl",
    ],
    "TCL_PACKAGES_MODULES": [
        "packages and modules in tcl", "run a package in tcl",
    ],
    "TCL_OBJECT_ORIENTED": [
        "object oriented paradigm in tcl", "support object oriented",
    ],
    # ---------- Tk ----------
    "TK_WIDGETS": [
        "properties of tk widget entry", "layout widgets", "mega widgets",
        "canvas widget options", "operations of buttons", "buttons", "canvas",
        "selection widgets", "login form", "login page",
        "list of available selection", "access tk features",
    ],
    "TK_GEOMETRY_MANAGERS": [
        "geometry managers", "pack geometry manager",
    ],
    "TK_EVENTS_BINDINGS": [
        "event handling and binding in tk", "binding commands to x events",
        "kind of events can be handled", "events are handled in tk", "event driven program",
        "events handled in tk", "bind command", "events in tk",
    ],
    "TK_IMAGES": [
        "options and available functions for creating an image",
    ],
    "TK_RELATIONSHIP_TCL": [
        "relationship between tcl and tk", "why tk is used",
        "tk module in ruby", "tk is related to other",
    ],
    "TK_VISUAL_TOOLKITS": [
        "tk-visual toolkits", "tk visual toolkits",
        "features and fundamental concepts of tk", "fundamental concepts of tk",
    ],
    # ---------- Ruby ----------
    "RUBY_SYNTAX_TYPES": [
        "lexical and syntactic structure", "syntactic structure of ruby",
        "ruby type system", "ruby type", "itrators in ruby", "iterator in ruby",
    ],
    "RUBY_OBJECTS": [
        "ruby objects in c", "object creation and cloning",
        "fixnum immediate value", "ruby objects",
    ],
    "RUBY_RUBYGEMS": [
        "rubygems", "ruby gems", "package management in ruby",
        "importance of rubygems",
    ],
    "RUBY_C_EXTENSION": [
        "own extensions in ruby", "extension code in c",
        "wrapping of c structures", "jukebox extension", "jukebox work",
        "ruby data type conversion", "stringvalue and stringvalueptr",
        "data type conversion functions and macros",
    ],
    "RUBY_CGI_COOKIES": [
        "cgi scripts using ruby", "cgi handles cookies",
        "cookies and sessions", "sample ruby cgi",
    ],
    "RUBY_EMBEDDING": [
        "embed ruby in your application", "role of ruby interpreter",
        "erb and eruby", "embedding of ruby to other languages", "embedding ruby in html",
    ],
    # ---------- Linux / UNIX ----------
    "LINUX_FILE_SYSTEM": [
        "file system of the linux", "linux file system", "default file system of linux",
        "ext3 file system", "file system operations", "filesystem functions in linux",
        "file system in detail", "file system in linux",
    ],
    "LINUX_FILE_MANAGEMENT": [
        "commands used for file management", "create files and directories in linux",
        "copying a file from one directory", "moving the files",
        "linux commands to perform file search", "procedure for searching a file",
        "search operation to find the fi", "file and directory search",
    ],
    "LINUX_PERMISSIONS_USERS": [
        "permissions for file", "chmod", "users and groups",
        "primary group", "secondary group", "standard symbols used to crea",
        "permissions in linux", "file access in unix",
    ],
    "LINUX_KERNEL_OS": [
        "linux kernel", "what is kernel", "kernel and explain its functions",
        "architecture of linux", "features and components of linux kernels",
        "what is linux and how does it work", "advantages and disadvantages of linux",
        "basic functionality of linux kernel", "general usage of linux kernel",
    ],
    "LINUX_COMPRESSION_ARCHIVING": [
        "zipping", "unzipping", "zipping concept", "tar.gz", "tar.bz2",
    ],
    "LINUX_TEXT_PROCESSING": [
        "commands used for text processing", "text processing in linux",
        "grep command",
    ],
    "LINUX_SHELL_COMMANDS": [
        "directory commands", "basic commands", "general usage of linux commands",
        "the following commands",
    ],
    "LINUX_NETWORK_CONFIGURATION": [
        "configure the network", "configure lan in linux", "red hat network features",
        "network interfaces that can be configured", "linux support networking",
    ],
    "LINUX_REMOTE_LOGIN": [
        "remote logins", "allow remote logins", "remote login to a system",
    ],
    "UNIX_SYSTEM_CALLS": [
        "system calls", "open()", "fork()", "read()", "seek()",
        "types of system calls", "process and a program",
        "process control commands", "process control command",
        "operating system interface facilities",
    ],
    # ---------- networking ----------
    "NETWORK_DNS": [
        "what is dns", "function of dns", "domain naming service",
        "how dns works", "configuration of dns", "network information services",
    ],
    "NETWORK_DHCP": [
        "dhcp", "dynamic host configuration protocol", "functions of dhcp",
    ],
    "NETWORK_FTP": [
        "ftp protocol", "file transfer protocol", "ftp site", "what is ftp",
    ],
    "NETWORK_NFS_SHARING": [
        "network file system", "nfs", "shared over the network",
        "etc/exports",
    ],
    "NETWORK_TCP_SOCKETS": [
        "tcp connection", "states of tcp", "bind(), listen()",
        "bind() , listen()", "listen() and accept()",
    ],
    "NETWORK_INTERNET_PROGRAMMING": [
        "dirty hands internet programming", "internet programming",
    ],
    # ---------- per-language catch-alls (declared last: specific wins) ----------
    "PERL_PROGRAMMING": ["perl"],
    "PHP_PROGRAMMING": ["php"],
    "PYTHON_PROGRAMMING": ["python"],
    "TCL_PROGRAMMING": ["tcl"],
    "TK_PROGRAMMING": ["tk"],
    "RUBY_PROGRAMMING": ["ruby"],
    "LINUX_UNIX_ADMINISTRATION": ["linux", "unix", "grep"],
    "NETWORKING_TECHNOLOGIES": ["network", "internet", "tcp", "server"],
}
SUBJECTS = [
    {
        "name": "Web Technologies",
        "dirs": ["WEB TECHNOLOGIES"],
        "fallback": "GENERAL_WEB_TECHNOLOGIES",
        "keywords": WEB_TECH_KEYWORDS,
        "add": KEYWORD_ADDITIONS["WEB_TECH"],
        "out": "Web_Technologies_Dataset.csv",
    },
    {
        "name": "Cloud Computing",
        "dirs": ["CLOUD COMPUTING"],
        "fallback": "GENERAL_CLOUD_COMPUTING",
        "keywords": CLOUD_KEYWORDS,
        "add": KEYWORD_ADDITIONS["CLOUD"],
        "out": "Cloud_Computing_Dataset.csv",
    },
    {
        "name": "Internet of Things",
        "dirs": ["INTERNET OF THINGS"],
        "fallback": "GENERAL_IOT",
        "keywords": IOT_KEYWORDS,
        "add": KEYWORD_ADDITIONS["IOT"],
        "out": "Internet_of_Things_Dataset.csv",
    },
    {
        "name": "Fundamentals of Internet of Things",
        "dirs": ["FUNDAMENTALS OF INTERNET OF THINGS"],
        "fallback": "GENERAL_IOT_FUNDAMENTALS",
        "keywords": IOT_FUND_KEYWORDS,
        "add": KEYWORD_ADDITIONS["IOT_FUND"],
        "out": "Fundamentals_of_IoT_Dataset.csv",
    },
    {
        "name": "Semantic Web and Social Networks",
        "dirs": ["SEMANTIC WEB AND SOCIAL NETWORKS"],
        "fallback": "GENERAL_SEMANTIC_WEB",
        "keywords": SEMANTIC_WEB_KEYWORDS,
        "add": {},
        "out": "Semantic_Web_and_Social_Networks_Dataset.csv",
    },
    {
        "name": "Advanced Algorithms",
        "dirs": ["ADVANCED ALGORITHMS"],
        "fallback": "GENERAL_ADVANCED_ALGORITHMS",
        "keywords": ADV_ALGO_KEYWORDS,
        "add": {},
        "exclude": ADV_ALGO_EXCLUDE,
        "excluded_out": "Advanced_Algorithms_Excluded.csv",
        "normalize_match": True,
        "out": "Advanced_Algorithms_Dataset.csv",
    },
    {
        "name": "Scripting Languages",
        "dirs": ["SCRIPTING LANGUAGES"],
        "fallback": "GENERAL_SCRIPTING_LANGUAGES",
        "keywords": SCRIPTING_KEYWORDS,
        "add": {},
        "normalize_match": True,
        "fold": {
            "TCL_OBJECT_ORIENTED": "TCL_PROGRAMMING",
            "TCL_PACKAGES_MODULES": "TCL_PROGRAMMING",
            "TCL_EVENTS": "TK_EVENTS_BINDINGS",
            "TK_IMAGES": "TK_WIDGETS",
            "PYTHON_STRING_FUNCTIONS": "PYTHON_DATA_TYPES",
            "PYTHON_MEMORY_MANAGEMENT": "PYTHON_DATA_TYPES",
            "PYTHON_OBJECT_ORIENTED": "PYTHON_FUNCTIONS",
            "PYTHON_TYPE_CASTING": "PYTHON_FUNCTIONS",
            "PYTHON_FILE_IO": "PYTHON_FUNCTIONS",
            "LINUX_TEXT_PROCESSING": "LINUX_SHELL_COMMANDS",
            "LINUX_REMOTE_LOGIN": "LINUX_NETWORK_CONFIGURATION",
            "RUBY_CGI_COOKIES": "WEB_SCRIPTING_AND_FORMS",
            "PERL_SCOPE_REFERENCES": "PERL_REFERENCES_SUBROUTINES",
            "PERL_TOOLKITS": "PERL_PROGRAMMING",
            "PERL_SECURITY": "PERL_PROGRAMMING",
            "PERL_OS_INTERNET_INTERFACING": "PERL_PROGRAMMING",
            "PHP_DATABASE_ACCESS": "PHP_PROGRAMMING",
            "PHP_ECHO_PRINT": "PHP_BASICS",
            "NETWORK_INTERNET_PROGRAMMING": "NETWORKING_TECHNOLOGIES",
            "NETWORK_TCP_SOCKETS": "NETWORKING_TECHNOLOGIES",
        },
        "out": "Scripting_Languages_Dataset.csv",
    },
]


def merge_keywords(base, extra):
    merged = {k: list(v) for k, v in base.items()}
    for topic, kws in extra.items():
        if topic not in merged:
            merged[topic] = []
        seen = set(merged[topic])
        for kw in kws:
            if kw not in seen:
                merged[topic].append(kw)
                seen.add(kw)
    return merged

PART_MARKER = re.compile(r"PART\s*[-–—]?\s*([AB])", re.I)
NOISE_LINE = re.compile(
    r"^\s*(?:"
    r"PART\s*[-–—]?\s*[AB]"
    r"|--+\s*oo\w*\s*--+"
    r"|used papers?.*"
    r"|\(?\s*computer science and engineer\w*\s*\)?"
    r"|and may have.*"
    r"|carries \d+ marks.*"
    r"|\d+\s*marks and may have.*"
    r"|\d+\s*marks\)?"
    r"|web technologies|cloud computing|internet of things|fundamentals of internet of things"
    r"|\s*R\d{2}\s*"
    r")\s*$",
    re.I,
)
# A question number followed by anything that is not another digit. The old
# [A-Za-z] lookahead silently failed to split questions that open with a quote
# mark (e.g. `3. "PERL implements ..."`), merging them into the previous block.
Q_SPLIT = re.compile(r"(?m)^(?=\d{1,2}\s*[.)]\s*(?!\d))")
LEAD_NUM = re.compile(r"^\s*\d{1,2}\s*[.)]\s*")
LEAD_SUB = re.compile(r"^\s*[a-j]\s*[.)]\s*")
BRACKET = re.compile(r"\[\s*\d+(?:\s*\+\s*\d+)*\s*\]")
SUB_LETTER = re.compile(r"(?<![A-Za-z0-9])([b-j])\s*[.)]\s+")
SPLIT_TEXT = re.compile(r"(?<=[.;:])\s+(?=[a-j]\)\s)")


def classify_topic(text, keywords, fallback):
    text_lower = text.lower()
    scores = {topic: 0 for topic in keywords}
    for topic, kws in keywords.items():
        for kw in kws:
            if kw in text_lower:
                scores[topic] += 1
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else fallback


def classify_bloom(text):
    t = text.lower()
    if any(w in t for w in ["design a", "propose", "formulate", "create a", "develop a", "construct"]):
        return "Create"
    if any(w in t for w in ["evaluate", "justify", "assess", "critique", "recommend", "judge"]):
        return "Evaluate"
    if any(w in t for w in ["analyze", "analyse", "compare", "differentiate", "distinguish",
                            "contrast", "examine", "why is it", "why does"]):
        return "Analyze"
    if any(w in t for w in ["apply", "calculate", "compute", "implement", "demonstrate",
                            "illustrate", "draw", "show", "write a program", "solve"]):
        return "Apply"
    if any(w in t for w in ["explain", "describe", "discuss", "elaborate", "interpret",
                            "summarize", "outline", "give an account", "briefly", "how does",
                            "how is", "how are", "how can", "how to"]):
        return "Understand"
    return "Remember"


def parse_marks(text):
    m = BRACKET.search(text)
    if not m:
        return None
    nums = [int(x) for x in re.findall(r"\d+", m.group(0))]
    return max(nums) if nums else None


def parse_mark_parts(text):
    m = BRACKET.search(text)
    if not m:
        return []
    return [int(x) for x in re.findall(r"\d+", m.group(0))]


def clean_question(text):
    text = BRACKET.sub("", text)
    text = re.sub(r"used papers?.*", "", text, flags=re.I)
    text = re.sub(r"--+\s*oo\w*\s*--+", "", text)
    text = re.sub(r"\bR\d{2}\b", "", text)
    text = re.sub(r"[\s.,;:]*\bOR\b\s*$", "", text)
    text = re.sub(r"^\s*OR\b\s*", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def is_garbage(text):
    t = text.strip().lower()
    if len(t) < 25:
        return True
    if re.search(r"may have.*sub question|^\(?\s*\d+\s*marks\s*\)?$|^used paper|^---|^ or$|^--oo"
                 r"|^explain the following:?$|^write short notes? on:?$|^define the following:?$"
                 r"|^discuss the following:?$|^with a neat diagram$|^and may have"
                 r"|short notes? on the following|write short note|explain the following"
                 r"|^the following$|following:$|^or$", t):
        return True
    return False


def strip_noise_lines(text):
    keep = []
    for line in text.splitlines():
        if NOISE_LINE.match(line):
            continue
        keep.append(line)
    return "\n".join(keep)


def split_subparts(body):
    body = LEAD_SUB.sub("", body.strip())
    positions = []
    for letter in "bcdefghij":
        m = SUB_LETTER.search(body)
        if m and m.group(1) == letter:
            positions.append(m.start())
            body = body[:m.start()] + " " + body[m.end():]
    positions.sort()
    parts = []
    prev = 0
    for p in positions:
        parts.append(body[prev:p])
        prev = p
    parts.append(body[prev:])
    out = []
    for p in parts:
        p = LEAD_SUB.sub("", p.strip()).strip()
        if p:
            out.append(p)
    return out


def split_sentences(body):
    body = SPLIT_TEXT.sub("\x00", body)
    chunks = [c.strip() for c in body.split("\x00") if c.strip()]
    if len(chunks) <= 1:
        return [LEAD_SUB.sub("", body.strip()).strip()]
    return [LEAD_SUB.sub("", c).strip() for c in chunks]


def parse_paper(path):
    raw = path.read_text(encoding="utf-8", errors="ignore")

    m_a = PART_MARKER.search(raw)
    part_a_text, part_b_text = "", raw
    if m_a and m_a.group(1).upper() == "A":
        m_b = PART_MARKER.search(raw, m_a.end())
        part_a_text = raw[m_a.end():m_b.start()] if m_b else raw[m_a.end():]
        part_b_text = raw[m_b.start():] if m_b else ""

    rows = []

    for chunk, part in ((strip_noise_lines(part_a_text), "A"),
                        (strip_noise_lines(part_b_text), "B")):
        if not chunk.strip():
            continue
        blocks = [b for b in Q_SPLIT.split(chunk) if len(b.strip()) > 10]
        for block in blocks:
            block = LEAD_NUM.sub("", block.strip())
            marks_all = parse_mark_parts(block)
            subparts = []
            for sp in split_subparts(block):
                subparts.extend(split_sentences(sp))
            if not subparts:
                continue
            for idx, sp in enumerate(subparts):
                marks = None
                if part == "A":
                    marks = parse_marks(sp)
                elif marks_all and len(marks_all) > 1 and idx < len(marks_all):
                    marks = marks_all[idx]
                elif marks_all:
                    marks = marks_all[0]
                if marks is None:
                    marks = 2 if part == "A" else 8
                rows.append({"text": sp, "marks": marks, "part": part})

    return rows


def extract_year(path):
    m = re.search(r"(\d{4})", path.name)
    if m:
        year = int(m.group(1))
        if 1990 <= year <= 2100:
            return year
    return None


def norm_for_match(text):
    """Collapse OCR damage so keyword matching survives it.

    The cleaned corpus still contains spaced hyphens ("NP - Complete"),
    en/em dashes ("Zero - one"), broken apostrophes ("Prim's"), accented
    letters ("Naive") and words split mid-token ("stri ng-matching").
    Stripping whitespace, hyphens and accents on BOTH the question and the
    keywords makes matching robust to all of these.
    """
    t = text.lower()
    t = t.replace("\u2013", "-").replace("\u2014", "-")
    t = t.replace("\u2018", "'").replace("\u2019", "'")
    t = "".join(c for c in unicodedata.normalize("NFKD", t)
                if not unicodedata.combining(c))
    return re.sub(r"[\s\-]+", "", t)


def main():
    OUTDIR.mkdir(parents=True, exist_ok=True)
    for cfg in SUBJECTS:
        files = []
        for d in cfg["dirs"]:
            files.extend(CORPUS.rglob(f"{d}/*.txt"))
        files = sorted(set(files))

        store = {}
        excl_store = {}
        stats = {"files": len(files), "used": 0, "skipped_undated": 0,
                 "raw": 0, "kept": 0, "dedup": 0, "excluded_asset": 0}
        exclude = cfg.get("exclude") or []
        kw_map = merge_keywords(cfg["keywords"], cfg["add"])
        # Fold thin concept tags into their natural sibling so no topic ends up
        # with fewer than 3 rows (the repo's documented minimum for training).
        for src_tag, dst_tag in (cfg.get("fold") or {}).items():
            if src_tag not in kw_map:
                continue
            kw_map.setdefault(dst_tag, [])
            for kw in kw_map[src_tag]:
                if kw not in kw_map[dst_tag]:
                    kw_map[dst_tag].append(kw)
            del kw_map[src_tag]
        norm_match = cfg.get("normalize_match", False)
        match_text = norm_for_match if norm_match else (lambda t: t)
        if norm_match:
            # Normalising collapses distinct keywords onto the same string
            # ("quick sort" and "quicksort"). Left in place they would each
            # score a hit and inflate that tag above its competitors.
            deduped = {}
            for t, kws in kw_map.items():
                seen, keep = set(), []
                for k in kws:
                    nk = norm_for_match(k)
                    if nk and nk not in seen:
                        seen.add(nk)
                        keep.append(nk)
                deduped[t] = keep
            kw_map = deduped

        for f in files:
            year = extract_year(f)
            if year is None:
                stats["skipped_undated"] += 1
                print(f"  [SKIP undated] {f.name}")
                continue
            stats["used"] += 1
            for r in parse_paper(f):
                stats["raw"] += 1
                q = clean_question(r["text"])
                if is_garbage(q):
                    continue
                key = re.sub(r"[^a-z0-9]+", " ", q.lower()).strip()

                reason = next((p.pattern for p in exclude if p.search(q)), None)
                if reason is not None:
                    stats["excluded_asset"] += 1
                    if key not in excl_store:
                        excl_store[key] = {
                            "subject_name": cfg["name"],
                            "raw_question_text": q,
                            "topic_tag": "",
                            "bloom_level": classify_bloom(q),
                            "original_marks": r["marks"],
                            "part_a_years": {year} if r["part"] == "A" else set(),
                            "part_b_years": {year} if r["part"] == "B" else set(),
                            "excluded_reason": reason,
                        }
                    else:
                        if r["part"] == "A":
                            excl_store[key]["part_a_years"].add(year)
                        else:
                            excl_store[key]["part_b_years"].add(year)
                    continue

                stats["kept"] += 1
                if key not in store:
                    store[key] = {
                        "subject_name": cfg["name"],
                        "raw_question_text": q,
                        "topic_tag": classify_topic(
                            match_text(q) if norm_match else q, kw_map, cfg["fallback"]
                        ),
                        "bloom_level": classify_bloom(q),
                        "original_marks": r["marks"],
                        "part_a_years": set(),
                        "part_b_years": set(),
                    }
                else:
                    stats["dedup"] += 1
                if r["part"] == "A":
                    store[key]["part_a_years"].add(year)
                else:
                    store[key]["part_b_years"].add(year)

        rows = []
        for v in store.values():
            rows.append({
                "subject_name": v["subject_name"],
                "raw_question_text": v["raw_question_text"],
                "topic_tag": v["topic_tag"],
                "bloom_level": v["bloom_level"],
                "original_marks": v["original_marks"],
                "part_a_years": str(sorted(v["part_a_years"])),
                "part_b_years": str(sorted(v["part_b_years"])),
            })

        out_path = OUTDIR / cfg["out"]
        with open(out_path, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=FIELDS)
            w.writeheader()
            w.writerows(rows)

        if excl_store:
            side = OUTDIR / cfg["excluded_out"]
            with open(side, "w", newline="", encoding="utf-8") as fh:
                w = csv.DictWriter(fh, fieldnames=FIELDS + ["excluded_reason"])
                w.writeheader()
                for v in excl_store.values():
                    w.writerow({
                        "subject_name": v["subject_name"],
                        "raw_question_text": v["raw_question_text"],
                        "topic_tag": v["topic_tag"],
                        "bloom_level": v["bloom_level"],
                        "original_marks": v["original_marks"],
                        "part_a_years": str(sorted(v["part_a_years"])),
                        "part_b_years": str(sorted(v["part_b_years"])),
                        "excluded_reason": v["excluded_reason"],
                    })
            print(f"  -> excluded side file: {side} ({len(excl_store)} rows)")

        tags = defaultdict(int)
        for r in rows:
            tags[r["topic_tag"]] += 1
        fb = tags.get(cfg["fallback"], 0)
        print(f"{cfg['name']}")
        print(f"  papers_found={stats['files']}  used={stats['used']}  "
              f"skipped_undated={stats['skipped_undated']}")
        print(f"  raw_parts={stats['raw']}  kept={stats['kept']}  "
              f"unique={len(rows)}  merged_dups={stats['dedup']}  "
              f"excluded_supplied_asset={stats['excluded_asset']}")
        print(f"  tags={len(tags)}  fallback_rows={fb} ({fb/max(len(rows),1)*100:.1f}%)")
        thin = sorted(n for t, n in tags.items() if n < 3)
        print(f"  tags_with_fewer_than_3_rows={len(thin)}"
              + (f"  -> {thin}" if thin else ""))
        print(f"  -> {out_path}")


if __name__ == "__main__":
    main()
