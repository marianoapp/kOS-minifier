import sys
import os.path
import re
from enum import Flag, auto
import collections
from operator import itemgetter


class MinFlags(Flag):
    NONE = auto()
    REMOVE_COMMENTS = auto()
    REMOVE_INDENTATION = auto()
    REMOVE_SPACES = auto()
    REMOVE_NEWLINES = auto()
    REPLACE_VARS = auto()
    ALIAS_FUNCTIONS = auto()
    ALIAS_CONSTANTS = auto()
    BIND_FUNCTIONS = auto()
    USE_SHORTCUTS = auto()
    HELP = auto()
    ALL = REMOVE_COMMENTS | REMOVE_INDENTATION | REMOVE_SPACES | REMOVE_NEWLINES | REPLACE_VARS | \
        ALIAS_FUNCTIONS | ALIAS_CONSTANTS | BIND_FUNCTIONS | USE_SHORTCUTS


grammar = {
    "not", "and", "or", "true", "false", "set", "to", "is", "if", "else", "until", "step", "do", "lock", "unlock",
    "print", "at", "on", "toggle", "wait", "when", "then", "off", "stage", "clearscreen", "add", "remove", "log",
    "break", "preserve", "declare", "defined", "local", "global", "parameter", "function", "return", "switch",
    "copy", "from", "rename", "volume", "file", "delete", "edit", "run", "runpath", "runoncepath", "once",
    "compile", "list", "reboot", "shutdown", "for", "unset", "choose", "in", "all", "lazyglobal"
}

bound_variables = {
    "config", "addons", "version", "kuniverse", "warpmode", "warp", "mapview", "activeship", "terminal", "archive",
    "core", "ship", "target", "hastarget", "status", "homeconnection", "controlconnection",
    "missiontime", "sessiontime", "solarprimevector", "donothing",
    "heading", "prograde", "retrograde", "facing", "maxthrust", "availablethrust", "velocity", "geoposition",
    "latitude", "longitude", "up", "north", "body", "angularmomentum", "angularvel", "angularvelocity", "mass",
    "verticalspeed", "surfacespeed", "groundspeed", "airspeed", "shipname", "vesselname", "altitude", "alt", "apoapsis",
    "periapsis", "sensors", "srfprograde", "srfretrograde", "obt", "orbit",
    "throttle", "steering", "steeringmanager", "wheelsteering", "wheelthrottle", "sasmode", "navmode",
    "sas", "gear", "legs", "chutes", "chutessafe", "lights", "panels", "radiators", "ladders",
    "legs", "bays", "deploydrills", "drills", "fuelcells", "isru", "intakes", "brakes", "rcs",
    "abort", "ag1", "ag2", "ag3", "ag4", "ag5", "ag6", "ag7", "ag8", "ag9", "ag10",
    "white", "black", "red", "green", "blue", "yellow", "magenta", "purple", "cyan", "grey", "gray",
    "encounter", "eta", "nextnode", "hasnode", "allnodes",
}

listables = {
    "bodies", "targets", "fonts", "processors", "resources", "parts", "engines", "elements", "rcs", "sensors",
    "dockingports", "files", "volumes"
}

builtin_functions = {
    "addalarm", "listalarms", "deletealarm", "buildlist", "vcrs", "vectorcrossproduct", "vdot", "vectordotproduct",
    "vxcl", "vectorexclude", "vang", "vectorangle", "clearscreen", "hudtext", "stage", "add", "remove", "warpto",
    "processor", "edit", "printlist", "node", "v", "r", "q", "createorbit", "rotatefromto", "lookdirup", "angleaxis",
    "latlng", "vessel", "body", "bodyexists", "bodyatmosphere", "bounds", "heading", "slidenote", "note", "getvoice",
    "stopallvoices", "time", "hsv", "hsva", "rgb", "rgba", "vecdraw", "vecdrawargs", "clearvecdraws", "clearguis",
    "gui", "positionat", "velocityat", "highlight", "orbitat", "career", "allwaypoints", "waypoint", "transferall",
    "transfer", "lex", "lexicon", "list", "pidloop", "queue", "stack", "uniqueset", "abs", "mod", "floor", "ceiling",
    "round", "sqrt", "ln", "log10", "min", "max", "random", "randomseed", "char", "unchar", "print", "printat",
    "toggleflybywire", "selectautopilotmode", "run", "logfile", "reboot", "shutdown", "debugdump", "debugfreezegame",
    "profileresult", "makebuiltindelegate", "droppriority", "copy_deprecated", "rename_file_deprecated",
    "rename_volume_deprecated", "delete_deprecated", "scriptpath", "switch", "cd", "chdir", "copypath", "movepath",
    "deletepath", "writejson", "readjson", "exists", "open", "create", "createdir", "range", "constant",
    "sin", "cos", "tan", "arcsin", "arccos", "arctan", "arctan2", "anglediff", "path", "volume"
}

reserved_words = grammar.union(bound_variables) \
                        .union(listables) \
                        .union(builtin_functions)

shortcuts = [
    # ship shortcuttable suffixes
    ["ship:heading", "heading"], ["ship:prograde", "prograde"], ["ship:retrograde", "retrograde"],
    ["ship:facing", "facing"], ["ship:maxthrust", "maxthrust"], ["ship:availablethrust", "availablethrust"],
    ["ship:velocity", "velocity"], ["ship:geoposition", "geoposition"], ["ship:latitude", "latitude"],
    ["ship:longitude", "longitude"], ["ship:up", "up"], ["ship:north", "north"], ["ship:body", "body"],
    ["ship:angularmomentum", "angularmomentum"], ["ship:angularvel", "angularvel"], ["ship:mass", "mass"],
    ["ship:verticalspeed", "verticalspeed"], ["ship:surfacespeed", "surfacespeed"], ["ship:groundspeed", "groundspeed"],
    ["ship:airspeed", "airspeed"], ["ship:shipname", "shipname"], ["ship:altitude", "altitude"],
    ["ship:apoapsis", "apoapsis"], ["ship:periapsis", "periapsis"], ["ship:sensor", "sensor"],
    ["ship:srfprograde", "srfprograde"], ["ship:srfretrograde", "srfretrograde"],
    # others
    ["time:seconds", "time"]
]

# TODO:
# - replace built-in functions with their short name (vectorexclude -> vxcl)
# - replace suffixes with their short name (orbit -> obt) DANGEROUS: can override custom suffixes


def minify(text, flags):
    # process file
    external_ids = parse_external_ids(text)
    # strip comments
    if MinFlags.REMOVE_COMMENTS in flags:
        text = remove_comments(text)
    # extract string literals and replace them with string_tokens
    text, string_tokens = tokenize_string_literals(text)
    # make lowercase, convert CRLF to LF
    text = simplify(text)
    # alias built-in functions
    if MinFlags.ALIAS_FUNCTIONS in flags:
        text = alias_builtin_functions(text)
    # alias constants
    if MinFlags.ALIAS_CONSTANTS in flags:
        text = alias_constants(text)
    # bind functions
    if MinFlags.BIND_FUNCTIONS in flags:
        text = bind_functions(text)
    # extract all identifiers (excluding keywords) and replace them with var_tokens
    if MinFlags.REPLACE_VARS in flags:
        text, var_tokens = tokenize_variables(text, external_ids)
    # replace variables with shortcuts
    if MinFlags.USE_SHORTCUTS in flags:
        text = replace_with_shortcuts(text)
    # remove whitespace
    text = remove_whitespace(text, flags)
    # replace string_tokens with the actual strings
    text = restore_string_literals(text, string_tokens)
    return text


def parse_external_ids(text):
    matches = re.findall(r"#EXTERNAL_IDS(.+)", text)
    merged_matches = ",".join(matches)
    ids = [x.strip().lower() for x in merged_matches.split(",")]
    return ids


def remove_comments(text):
    return re.sub(r"\s*//.+", "", text)


def tokenize_string_literals(text):
    regex = re.compile(r"\".+?\"")
    new_text = text
    tokens = []
    last_index = 1
    for match in regex.finditer(text):
        token_id = "%s" + str(last_index)
        token_text = match.group(0)
        tokens.append([token_id, token_text])
        new_text = new_text.replace(token_text, token_id, 1)
        last_index += 1
    return new_text, tokens


def simplify(text):
    # make lower case
    text = text.lower()
    # replace CRLF with LF
    text = text.replace("\r\n", "\n")
    return text


def alias_builtin_functions(text):
    # find all identifiers that appear more than once
    identifiers = find_count_identifiers(r"(?<![:%])\b[a-z]\w*(?=[(@])", text, 2)
    functions = [[item, count] for item, count in identifiers if item in builtin_functions]
    # filter functions for which make sense creating an alias
    alias_template = "local {0} to {1}@."
    alias_template_len = get_alias_template_length(alias_template)
    functions_to_alias = [item for item, count in functions
                          if alias_template_len + len(item) + count * 2 < len(item) * count]
    # create aliases and replace them in the text
    aliases = []
    repl_pattern = r"(?<![:%])\b{FUNCNAME}(?=[(@])"
    for function_name in functions_to_alias:
        alias_name = "alias__" + function_name
        aliases.append([alias_name, function_name])
        text = re.sub(repl_pattern.replace("{FUNCNAME}", function_name), alias_name, text)
    # append aliases at the beginning of the file.
    alias_decl = []
    for alias in aliases:
        var_instruction = alias_template.format(*alias)
        alias_decl.append(var_instruction)
    text = "\n".join(alias_decl) + "\n" + text
    return text


def alias_constants(text):
    # find all constants that appear more than once
    constants = find_count_identifiers(r"(?<![:%])\bconstant:[a-z0-9]\w*", text, 2)
    # filter identifiers for which make sense creating an alias
    alias_template = "local {0} to {1}."
    alias_template_len = get_alias_template_length(alias_template)
    constants_to_alias = [item for item, count in constants
                          if alias_template_len + len(item) + count * 2 < len(item) * count]
    # create aliases and replace them in the text
    aliases = []
    repl_pattern = r"(?<![:%])\b{CONSTANT}\b"
    for constant_name in constants_to_alias:
        alias_name = "alias__" + constant_name.replace(":", "_")
        aliases.append([alias_name, constant_name])
        text = re.sub(repl_pattern.replace("{CONSTANT}", constant_name), alias_name, text)
    # check if it makes sense to create an alias for the "constant" object
    constant_count = sum([count for item, count in constants if item not in constants_to_alias]) + len(aliases)
    # TODO: improve
    if alias_template_len + len("constant") + constant_count * 2 < len("constant") * constant_count:
        constant_name = "constant"
        alias_name = "alias__" + constant_name
        # replace the new name in existing aliases
        aliases = [[an, cn.replace(constant_name, alias_name)] for an, cn in aliases]
        aliases.insert(0, [alias_name, constant_name])
        text = re.sub(repl_pattern.replace("{CONSTANT}", constant_name), alias_name, text)
    # append aliases at the beginning of the file.
    alias_decl = []
    for alias in aliases:
        var_instruction = alias_template.format(*alias)
        alias_decl.append(var_instruction)
    text = "\n".join(alias_decl) + "\n" + text
    return text


def bind_functions(text):
    # find function calls that appear more than once with constant arguments
    function_calls = find_count_identifiers(r"(?<![:%])\b((v|r|q)\(([0-9,]+)\))", text, 2)
    # filter functions calls for which make sense creating an alias
    alias_template = "local {0} to {1}@:bind({2})."
    alias_template_len = get_alias_template_length(alias_template)
    functions_to_alias = [item for item, count in function_calls
                          if alias_template_len + len(item[0]+item[1]) + count * 4 < len(item[0]+item[1]) * count]
    # create aliases and replace them in the text
    aliases = []
    repl_pattern = r"(?<![:%])\b{FUNCCALL}"
    for func_call, func_name, arguments in functions_to_alias:
        alias_name = "alias__" + func_name + arguments.replace(",", "_")
        aliases.append([alias_name, func_name, arguments])
        text = re.sub(repl_pattern.replace("{FUNCCALL}", re.escape(func_call)), alias_name + "()", text)
    # append aliases at the beginning of the file.
    alias_decl = []
    for alias in aliases:
        var_instruction = alias_template.format(*alias)
        alias_decl.append(var_instruction)
    text = "\n".join(alias_decl) + "\n" + text
    return text


def find_count_identifiers(pattern, text, min_count=1):
    identifiers = re.findall(pattern, text)
    # unique identifiers with a count of how many times they appear in the text
    identifiers = [[item, count] for item, count in collections.Counter(identifiers).items()
                   if count >= min_count]
    return identifiers


def get_alias_template_length(alias_template, minified_identifier_length=2):
    # remove the replacement placeholders
    alias_length = len(re.sub(r"\{[0-9]\}", "", alias_template))
    # add the expected minified identifier length
    alias_length += minified_identifier_length
    # add one character for the trailing space/newline
    alias_length += 1
    return alias_length


def tokenize_variables(text, external_ids):
    identifiers = find_count_identifiers(r"(?<![:%])\b[a-z]\w*", text)
    # exclude all identifiers that are in the reserved_words list
    ids_exclude = reserved_words.union(external_ids)
    identifiers = [[item, count] for item, count in identifiers if item not in ids_exclude]
    # sort identifiers so the most common ones get the shorter names
    identifiers_tokenize = [item for item, _ in sorted(identifiers, key=itemgetter(1), reverse=True)]
    # replace identifiers with tokens
    tokens = []
    last_index = 1
    repl_pattern = r"(?<![:%])\b{VARNAME}\b"
    for token_text in identifiers_tokenize:
        token_id = "%v" + str(last_index)
        tokens.append([token_id, token_text])
        text = re.sub(repl_pattern.replace("{VARNAME}", token_text), token_id, text)
        last_index += 1
    # replace tokens with new var names
    token_dict = {}
    skip = 0
    for tok in tokens:
        index = int(tok[0][2:])
        while True:
            new_var_name = index_to_var_name(index + skip)
            if new_var_name not in ids_exclude:
                break
            skip += 1
        token_dict[tok[0]] = new_var_name
    for tok in reversed(tokens):
        new_var_name = token_dict[tok[0]]
        text = text.replace(tok[0], new_var_name)
        tok[0] = new_var_name
    return text, tokens


def index_to_var_name(index):
    string = [" "] * 5
    i = 0
    while index > 0:
        rem = index % 26
        if rem == 0:
            string[i] = 'z'
            i += 1
            index = (index // 26) - 1
        else:
            string[i] = chr((rem - 1) + ord('a'))
            i += 1
            index = index // 26
    string = string[::-1]
    return "".join(string).lstrip()


def replace_with_shortcuts(text):
    repl_pattern = r"(?<![:%])\b{VARNAME}\b"
    for old, new in shortcuts:
        text = re.sub(repl_pattern.replace("{VARNAME}", old), new, text)
    return text


def remove_whitespace(text, flags):
    # regex patterns
    special_chars = r"+\-/*\^<>=\(\)\{\}\[\],:#"
    patterns = [
                [r"[ \t]+$", r""],                          # remove trailing whitespace
                [r"\n{2,}", r"\n"]                          # replace multiple newlines with a single one
               ]
    if MinFlags.REMOVE_INDENTATION in flags:
        patterns.append([r"^[ \t]+", r""])                  # remove leading whitespace
        patterns.append([r"[ \t]{2,}", r" "])               # replace whitespace with a single space
    if MinFlags.REMOVE_NEWLINES in flags:
        patterns.append([r"\n+", r" "])                     # replace newlines with a space
    if MinFlags.REMOVE_SPACES in flags:
        patterns.append([r"[ \t]([{SPECIAL}])", r"\1"])     # remove whitespace on the left
        patterns.append([r"([{SPECIAL}])[ \t]", r"\1"])     # remove whitespace on the right
    # apply the replacements
    for p in patterns:
        p[0] = p[0].replace("{SPECIAL}", special_chars)
        text = re.sub(p[0], p[1], text, flags=re.MULTILINE)
    return text


def restore_string_literals(text, string_tokens):
    for token in reversed(string_tokens):
        text = text.replace(token[0], token[1], 1)
    return text


def read_file(file_name):
    # open the file
    if os.path.exists(file_name):
        with open(file_name, "r") as f:
            text = f.read()
    else:
        print("File not found!")
        return ""
    return text


def print_help():
    help_message = """Usage: minifier.py [options] file

  -a, --all                 apply all transformations (default option if none specified)
  -c, --remove-comments     remove comments
  -i, --remove-indentation  remove leading whitespace
  -s, --remove-spaces       remove spaces within instructions
  -n, --remove-newlines     merge the script into a single line
  -v, --replace-vars        replace variable names with shorter ones
      -f, --alias-functions     create aliases for commonly used built-in functions
      -o, --alias-constants     create aliases for commonly used built-in constants
      -b, --bind-functions      create aliases binding functions with constant arguments 
  -u, --use-shortcuts       replace game variables with their shorter form
      --help                print this help and exit

The uppercase version of the single letter flags have the opposite effect
e.g. -aN applies all transformations except removing newlines
"""
    print(help_message)


def parse_options(options):
    short_opts = [x.replace("-", "") for x in options if re.match(r"^-[a-zA-Z]+", x)]
    short_opts = [char for char in "".join(short_opts)]
    long_opts = [x.replace("--", "") for x in options if re.match(r"^--[a-z\-]+", x)]
    opts = short_opts + long_opts
    # available flags
    all_flags = [[MinFlags.ALL, ["a", "all"], []],
                 [MinFlags.REMOVE_COMMENTS, ["c", "remove-comments"], ["C"]],
                 [MinFlags.REMOVE_INDENTATION, ["i", "remove-indentation"], ["I"]],
                 [MinFlags.REMOVE_SPACES, ["s", "remove-spaces"], ["S"]],
                 [MinFlags.REMOVE_NEWLINES, ["n", "remove-newlines"], ["N"]],
                 [MinFlags.REPLACE_VARS, ["v", "replace-vars"], ["V"]],
                 [MinFlags.ALIAS_FUNCTIONS, ["f", "alias-functions"], ["F"]],
                 [MinFlags.ALIAS_CONSTANTS, ["o", "alias-constants"], ["O"]],
                 [MinFlags.BIND_FUNCTIONS, ["b", "bind-functions"], ["B"]],
                 [MinFlags.USE_SHORTCUTS, ["u", "use-shortcuts"], ["U"]],
                 [MinFlags.HELP, ["help"], []]]
    flags_dict = {opt: flag[0] for flag in all_flags for opt in flag[1]}
    neg_flags_dict = {opt: flag[0] for flag in all_flags for opt in flag[2]}
    # parse positive flags
    flags = MinFlags.NONE
    for o in opts:
        if o in flags_dict:
            flags |= flags_dict[o]
        elif o not in neg_flags_dict:
            print("'{0}' is not a valid option".format(o))
            return None
    # if no flags were specified use the default value
    if flags == MinFlags.NONE:
        flags = MinFlags.ALL
    # parse negative flags
    for o in opts:
        if o in neg_flags_dict:
            flags ^= neg_flags_dict[o]
    # validate flags combination
    flags_require_replace = [MinFlags.ALIAS_FUNCTIONS, MinFlags.ALIAS_CONSTANTS, MinFlags.BIND_FUNCTIONS]
    if any([f for f in flags_require_replace if f in flags]) and MinFlags.REPLACE_VARS not in flags:
        print("Some flags require variable replacing to be enabled")
        return None
    return flags


def main():
    text = ""
    read_from_file = sys.stdin.isatty()
    # check if the script is being called directly from a terminal
    if read_from_file:
        if len(sys.argv) == 1:
            print_help()
            return
    else:
        text = sys.stdin.read()
    # parse options
    options = [opt for opt in sys.argv[1:] if opt.startswith("-")]
    flags = parse_options(options)
    if flags is None:
        return
    if MinFlags.HELP in flags:
        print_help()
        return
    # minify the text
    if read_from_file:
        # assumes the file name is the last argument
        text = read_file(sys.argv[-1])
        if len(text) == 0:
            return
    result = minify(text, flags)
    print(result)


if __name__ == "__main__":
    main()
