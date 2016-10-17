# NotePublisher
```
Usage:
  notepublisher.py [-c FILE] [-o DIR] [--matchstack=STRING] [--matchnotebook=STRING] [--formats=PATTERNS]
  notepublisher.py --version

Options:
  -h --help  show this help message and exit
  --version  show version and exit
  -v --verbose  print status messages
  -o DIR --output=DIR  output directory [default: ./]
  -c FILE --config=FILE  config settings directory [default: ./notepublisher.cfg]
  --matchstack=STRING  string to match stack names against when searching
  --matchnotebook=STRING  string to match notebook names against when searching
  --formats=PATTERNS   export notes to file formats which match these comma
                       separated patterns [default: html,enex]

```

## Evernote API Keys
To use, you'll need production API keys from Evernote.  Enter your keys into a JSON config file similar to this one:
```
{
   "output" : "/Users/testuser/Documents/NotePublisher",
   "consumer_key" : "yyyyyyyyyyyyy",
   "consumer_secret": "zzzzzzzzzzzzzzzzzzzzzzzz",
   "dev_auth_token": "zzzzzzzzzzzzzzzzzzzzzzzzyyyyyyyyyyyyyyyyyyyyyyyyyyzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz"
}
```
and then specify it on the command line as 
```
notepublisher.py <my options> -c myconfig.cfg
```

