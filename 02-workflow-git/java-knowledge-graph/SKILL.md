---
name: java-knowledge-graph
description: Analyze JVM projects (Java/Kotlin/Scala/Groovy) with tree-sitter parsing, supporting Maven/Gradle/Ant/Ivy, generating knowledge graphs with visualizations
---

# Java Knowledge Graph Generator

Tree-sitter based analyzer for JVM projects. Supports **Java, Kotlin, Scala, Groovy** with **Maven, Gradle, Ant, Ivy**.

## Quick Start

```bash
# 1. First-time setup (one-time, ~1 minute)
pip3 install --user 'tree-sitter<0.21'
python3 scripts/install_grammars.py

# 2. Optional: Install Graphviz for SVG generation
brew install graphviz  # macOS
# sudo apt install graphviz  # Linux

# 3. Analyze project
python3 scripts/build_knowledge_graph.py /path/to/project output-dir
```

## What It Does

**Detects:**
- Build systems: Maven (pom.xml), Gradle (build.gradle*), Ant (build.xml), Ivy (ivy.xml)
- Languages: Java, Kotlin, Scala, Groovy (via tree-sitter AST parsing)
- Structure: Modules, packages, classes, interfaces, enums, annotations
- Relationships: Inheritance, implementations, module dependencies
- Patterns: Architecture layers (controller/service/repository/model/config/util)

**New in v2.0:**
- ✅ Config file parsing: `application*.properties`, `application*.yaml/yml`
- ✅ Gradle subprojects: `settings.gradle` parsing
- ✅ Properties loaded into module metadata
- ✅ Single-project fallback: Generates complete project diagram when no modules detected
- ✅ Fixed: Module names with hyphens now work in DOT/SVG generation

**Outputs:**
- `knowledge-graph.json` - Complete graph (nodes + edges)
- `module-dependencies.{dot,svg}` - Module dependency diagram
- `module-{name}.{dot,svg}` - Per-module class diagrams
- `project-{name}.{dot,svg}` - Complete project diagram (for single-module projects)

## Usage Examples

```bash
# Maven multi-module project
python3 scripts/build_knowledge_graph.py ~/workspace/my-spring-app kg-out

# Gradle project
python3 scripts/build_knowledge_graph.py ~/workspace/my-kotlin-app kg-out

# Single-module or no build system
python3 scripts/build_knowledge_graph.py ~/workspace/plain-java kg-out
```

## Querying the Knowledge Graph

### Schema Reference

**Node Types:**
- `system` - Root project node
- `module` - Maven/Gradle module or subproject
- `class` - Class declaration
- `interface` - Interface declaration
- `enum` - Enum declaration
- `annotation` - Annotation type declaration

**ID Naming Patterns:**
- System: `"system:{project_name}"` → `"system:nocode-saas"`
- Module: `"module:{artifactId}:{version}"` → `"module:nocode-saas:1.0.0"`
- Class: `"class:{fully.qualified.ClassName}"` → `"class:com.example.UserService"`
- Interface: `"interface:{fully.qualified.InterfaceName}"`
- Enum: `"enum:{fully.qualified.EnumName}"`

**Edge Types:**
- `contains` - System contains modules, modules contain classes
- `depends_on` - Module dependencies (with `scope` field: compile/test/runtime/provided)
- `extends` - Class inheritance
- `implements` - Interface implementation
- `aggregates` - Parent-child module relationships

**Key Node Fields:**
- `type` - Node type (system/module/class/interface/enum/annotation)
- `name` - Display name
- `moduleName` - Parent module (for classes)
- `package` - Package name (for classes)
- `layer` - Architecture layer (controller/service/repository/model/config/util/other)
- `language` - java/kotlin/scala/groovy
- `annotations` - Array of annotation names (e.g., `["@RestController", "@Lombok"]`)

**Key Edge Fields:**
- `from` - Source node ID
- `to` - Target node ID
- `type` - Edge type
- `scope` - Dependency scope (for `depends_on` edges)

---

### jq Queries (Recommended)

Install jq first:
- macOS: `brew install jq`
- Ubuntu/Debian: `sudo apt install jq`
- Fedora/RHEL: `sudo dnf install jq`
- Windows: `scoop install jq` or `choco install jq`

**Basic Queries:**

```bash
# List all modules
jq '.nodes[] | select(.type=="module") | .name' knowledge-graph.json

# Count classes by layer
jq '[.nodes[] | select(.type=="class")] | group_by(.layer) | 
    map({layer: .[0].layer, count: length})' knowledge-graph.json

# Find controllers
jq '.nodes[] | select(.layer=="controller") | .name' knowledge-graph.json

# Classes per module
jq -r '[.nodes[] | select(.type=="class")] | 
        group_by(.moduleName) | 
        map("\(.[0].moduleName): \(length) classes") | 
        .[]' knowledge-graph.json
```

**Module Dependency Queries:**

```bash
# List all module dependencies with scope
jq -r '.edges[] | select(.type=="depends_on") | 
       "\(.from | split(":")[1]) → \(.to | split(":")[1]) [\(.scope)]"' knowledge-graph.json

# Count dependencies per module
jq -r '[.edges[] | select(.type=="depends_on")] | 
        group_by(.from | split(":")[1]) | 
        map("\(.[0].from | split(":")[1]): \(length) dependencies") | 
        sort | .[]' knowledge-graph.json

# Find leaf modules (no outgoing dependencies)
jq -r '([.nodes[] | select(.type=="module") | .id] - 
        [.edges[] | select(.type=="depends_on") | .from] | unique) | 
        map(split(":")[1]) | .[]' knowledge-graph.json

# Modules most depended upon (most critical)
jq -r '[.edges[] | select(.type=="depends_on") | .to | split(":")[1]] | 
        group_by(.) | map({module: .[0], count: length}) | 
        sort_by(-.count) | .[:5] | 
        map("\(.module): \(.count) modules depend on it") | .[]' knowledge-graph.json

# Dependencies by scope
jq '[.edges[] | select(.type=="depends_on")] | 
     group_by(.scope) | map({scope: .[0].scope, count: length})' knowledge-graph.json

# Find circular dependencies
jq -r '[.edges[] | select(.type=="depends_on") | {from: .from, to: .to}] as $deps | 
        $deps[] | . as $d | 
        select($deps | any(.from == $d.to and .to == $d.from)) | 
        "\(.from | split(":")[1]) ↔ \(.to | split(":")[1])"' knowledge-graph.json | sort -u
```

**Advanced Queries:**

```bash
# Get project statistics summary
jq '{modules: [.nodes[] | select(.type=="module")] | length,
     classes: [.nodes[] | select(.type=="class")] | length,
     interfaces: [.nodes[] | select(.type=="interface")] | length,
     enums: [.nodes[] | select(.type=="enum")] | length,
     dependencies: [.edges[] | select(.type=="depends_on")] | length}' knowledge-graph.json

# List all classes with their annotations in a specific module
jq -r '.nodes[] | select(.type=="class" and .moduleName=="<module-name>") | 
       "\(.name) \(.annotations // [] | join(", "))"' knowledge-graph.json

# Find all classes extending a specific superclass
jq -r '.nodes[] | select(.superclass != null and (.superclass | contains("BaseController"))) | 
       "\(.moduleName)/\(.name)"' knowledge-graph.json

# Export module dependency pairs as CSV
jq -r '.edges[] | select(.type=="depends_on") | 
       [(.from | split(":")[1]), (.to | split(":")[1]), .scope] | @csv' knowledge-graph.json

# Export class list as CSV
jq -r '.nodes[] | select(.type=="class") | 
       [.moduleName, .package, .name, .layer, .language] | @csv' knowledge-graph.json
```

For more jq examples: https://jqlang.github.io/jq/manual/

---

### Python Queries (Alternative)

```python
import json

with open('knowledge-graph.json', 'r') as f:
    kg = json.load(f)

# List all modules
modules = [n['name'] for n in kg['nodes'] if n['type'] == 'module']
print("Modules:", modules)

# Count classes by layer
from collections import Counter
classes = [n for n in kg['nodes'] if n['type'] == 'class']
layer_counts = Counter(c.get('layer', 'other') for c in classes)
for layer, count in sorted(layer_counts.items()):
    print(f"{layer}: {count}")

# Find controllers
controllers = [n['name'] for n in kg['nodes'] if n.get('layer') == 'controller']
print("Controllers:", controllers)

# Module dependencies
for e in kg['edges']:
    if e['type'] == 'depends_on':
        print(f"  {e['from'].split(':')[1]} → {e['to'].split(':')[1]} [{e['scope']}]")
```

## Visualization

**Module Dependencies:**
- Blue arrows = compile dependencies
- Gray dashed = parent-child aggregation

**Class Diagrams (per-module):**
- Blue = controllers
- Green = services
- Yellow = repositories
- Pink = models/entities
- Purple = config
- Gray = utilities

## Troubleshooting

**"No classes found"**
- Check for `src/main/java/` or similar structure
- Supports flexible paths (not just Maven standard layout)

**"SVG generation skipped"**
- Normal if Graphviz not installed
- Generate manually: `dot -Tsvg file.dot -o file.svg`

**Large projects slow**
- Normal for 500+ files
- Shows progress during parsing

**Grammar compilation fails**
- Install C compiler: `xcode-select --install` (macOS) or `build-essential` (Linux)

## Integration

```bash
# CI/CD - generate as build artifact
python3 scripts/build_knowledge_graph.py . ci-kg
tar -czf kg.tar.gz ci-kg/

# Git hook - regenerate on commit
python3 scripts/build_knowledge_graph.py . docs/architecture
git add docs/architecture/
```

## Technical Notes

- **Parser:** tree-sitter (syntax-aware AST), ElementTree (XML for pom.xml)
- **No regex hacks:** Accurate language parsing via grammars
- **Performance:** ~3s for 621 files, 13 modules
- **Memory:** ~150MB for typical projects
- **Cross-language:** Mix Java/Kotlin/Scala in one project

## File Structure Expectations

```
project/
├── pom.xml (Maven)
│   └── <modules> detected → multi-module
├── build.gradle[.kts] (Gradle)
│   └── settings.gradle → subprojects
├── src/main/java/ (or other patterns)
│   └── com/example/*.java
├── src/main/kotlin/ (Kotlin)
├── src/main/scala/ (Scala)
└── src/main/resources/
    ├── application.properties ← parsed
    └── application.yaml ← parsed
```

## Support

- Check generated `README.md` in output dir
- Grammar issues? Re-run `scripts/install_grammars.py`
