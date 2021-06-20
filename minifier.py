import sys
import os.path
import re
from enum import Flag, auto


class MinFlags(Flag):
    NONE = auto()
    REMOVE_COMMENTS = auto()
    REMOVE_INDENTATION = auto()
    REMOVE_SPACES = auto()
    REMOVE_NEWLINES = auto()
    REPLACE_VARS = auto()
    HELP = auto()
    ALL = REMOVE_COMMENTS | REMOVE_INDENTATION | REMOVE_SPACES | REMOVE_NEWLINES | REPLACE_VARS


reserved_words = [
    # grammar
    "not", "and", "or", "true", "false", "set", "to", "is", "if", "else", "until", "step", "do", "lock", "unlock",
    "print", "at", "on", "toggle", "wait", "when", "then", "off", "stage", "clearscreen", "add", "remove", "log",
    "break", "preserve", "declare", "defined", "local", "global", "parameter", "function", "return", "switch",
    "copy", "from", "rename", "volume", "file", "delete", "edit", "run", "runpath", "runoncepath", "once",
    "compile", "list", "reboot", "shutdown", "for", "unset", "choose", "in", "all", "lazyglobal",
    # bound variables
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
    # listables
    "bodies", "targets", "fonts", "processors", "resources", "parts", "engines", "elements", # "rcs", "sensors",
    "dockingports", "files", "volumes",
    # built-in functions
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
]


def minify(file_name, flags):
    # open the file
    if os.path.exists(file_name):
        with open(file_name, "r") as f:
            text = f.read()
    else:
        print("File not found!")
        return ""
    # process file
    external_ids = parse_external_ids(text)
    # strip comments
    if MinFlags.REMOVE_COMMENTS in flags:
        text = remove_comments(text)
    # extract string literals and replace them with string_tokens
    text, string_tokens = tokenize_string_literals(text)
    # make lowercase, convert CRLF to LF
    text = simplify(text)
    # extract all identifiers (excluding keywords) and replace them with var_tokens
    if MinFlags.REPLACE_VARS in flags:
        text, var_tokens = tokenize_variables(text, external_ids)
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


def tokenize_variables(text, external_ids):
    # the negative lookbehind skip suffixes and string tokens
    regex = re.compile(r"(?<![:%])\b[a-z]\w*")
    # find all identifiers
    matches = regex.findall(text)
    # get unique identifiers
    # matches = list(set(matches))
    matches = list(dict.fromkeys(matches))
    # exclude all identifiers that are in the reserved_words list
    ids_exclude = reserved_words + external_ids
    matches = [x for x in matches if x not in ids_exclude]
    # replace identifiers with tokens
    tokens = []
    last_index = 1
    repl_pattern = r"(?<![:%])\b{VARNAME}\b"
    for match in matches:
        token_id = "%v" + str(last_index)
        token_text = match
        tokens.append([token_id, token_text])
        text = re.sub(repl_pattern.replace("{VARNAME}", token_text), token_id, text)
        last_index += 1
    # replace tokens with new var names
    for tok in reversed(tokens):
        index = int(tok[0][2:])
        new_var_name = index_to_var_name(index)
        # avoid variable names that are reserved words, like "v" and "r"
        while new_var_name in ids_exclude:
            new_var_name = "_" + new_var_name
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


def print_help():
    help_message = """Usage: minifier.py [options] file

  -a, --all                 apply all transformations (default option if none specified)
  -c, --remove-comments     remove comments
  -i, --remove-indentation  remove leading whitespace
  -s, --remove-spaces       remove spaces within instructions
  -n, --remove-newlines     merge the script into a single line
  -v, --replace-vars        replace variable names with shorter ones
      --help                print this help and exit
"""
    print(help_message)


def parse_options(options):
    short_opts = [x.replace("-", "") for x in options if re.match(r"^-[a-z]+", x)]
    short_opts = [char for char in "".join(short_opts)]
    long_opts = [x.replace("--", "") for x in options if re.match(r"^--[a-z\-]+", x)]
    opts = short_opts + long_opts
    # available flags
    all_flags = [[MinFlags.ALL, ["a", "all"]],
                 [MinFlags.REMOVE_COMMENTS, ["c", "remove-comments"]],
                 [MinFlags.REMOVE_INDENTATION, ["i", "remove-indentation"]],
                 [MinFlags.REMOVE_SPACES, ["s", "remove-spaces"]],
                 [MinFlags.REMOVE_NEWLINES, ["n", "remove-newlines"]],
                 [MinFlags.REPLACE_VARS, ["v", "replace-vars"]],
                 [MinFlags.HELP, ["help"]]]
    flags_dict = {opt: flag[0] for flag in all_flags for opt in flag[1]}
    # parse selected flags
    flags = MinFlags.NONE
    for o in opts:
        if o in flags_dict:
            flags |= flags_dict[o]
        else:
            print("'%s' is not a valid option" % o)
    return flags


def main():
    if len(sys.argv) == 1:
        print_help()
        return
    else:
        options = [opt for opt in sys.argv[1:] if opt.startswith("-")]
        flags = parse_options(options)
        if MinFlags.HELP in flags:
            print_help()
            return
        else:
            if flags == MinFlags.NONE:
                flags = MinFlags.ALL
            # TODO: make more robust
            # assume the file name is the last argument
            file_name = sys.argv[-1]
            result = minify(file_name, flags)
            print(result)


if __name__ == "__main__":
    main()
