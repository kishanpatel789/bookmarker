# `bookmarker`

**Usage**:

```console
$ bookmarker [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--install-completion`: Install completion for the current shell.
* `--show-completion`: Show completion for the current shell, to copy it or customize the installation.
* `--help`: Show this message and exit.

**Commands**:

* `init`: Initialize local configuration (database...
* `add`: Add an artifact with a title and URL.
* `delete`: Delete an artifact.
* `list`: List all artifacts.
* `show`: Show details for the specified artifact ID.
* `search`: Search for artifacts by title, URL, and tag
* `tag`: Add or remove tags from an artifact.
* `fetch`: Fetch content for the specified artifact ID.
* `fetch-many`: Fetch multiple artifacts concurrently.
* `summarize`: Summarize content for the specified...
* `summarize-many`: Summarize multiple artifacts concurrently.

## `bookmarker init`

Initialize local configuration (database and AI summarizer)

**Usage**:

```console
$ bookmarker init [OPTIONS]
```

**Options**:

* `--help`: Show this message and exit.

## `bookmarker add`

Add an artifact with a title and URL.

**Usage**:

```console
$ bookmarker add [OPTIONS] TITLE URL
```

**Arguments**:

* `TITLE`: The name of the artifact  [required]
* `URL`: The URL of the artifact  [required]

**Options**:

* `--artifact-type [article|youtube]`: The type of the artifact  [default: article]
* `--auto / --no-auto`: Auto fetch and summarize content  [default: auto]
* `--help`: Show this message and exit.

## `bookmarker delete`

Delete an artifact.

**Usage**:

```console
$ bookmarker delete [OPTIONS] ARTIFACT_ID
```

**Arguments**:

* `ARTIFACT_ID`: The ID of the artifact to delete  [required]

**Options**:

* `--help`: Show this message and exit.

## `bookmarker list`

List all artifacts.

**Usage**:

```console
$ bookmarker list [OPTIONS]
```

**Options**:

* `--help`: Show this message and exit.

## `bookmarker show`

Show details for the specified artifact ID.

**Usage**:

```console
$ bookmarker show [OPTIONS] ARTIFACT_ID
```

**Arguments**:

* `ARTIFACT_ID`: The ID of the artifact to show  [required]

**Options**:

* `--help`: Show this message and exit.

## `bookmarker search`

Search for artifacts by title, URL, and tag

**Usage**:

```console
$ bookmarker search [OPTIONS] TERM
```

**Arguments**:

* `TERM`: Text to search title and URL of artifacts  [required]

**Options**:

* `--tag TEXT`: Filter results by tag name
* `--help`: Show this message and exit.

## `bookmarker tag`

Add or remove tags from an artifact.

**Usage**:

```console
$ bookmarker tag [OPTIONS] ARTIFACT_ID TAGS...
```

**Arguments**:

* `ARTIFACT_ID`: The ID of artifact to update  [required]
* `TAGS...`: Tags to add or remove  [required]

**Options**:

* `--remove`: Remove tag instead of adding
* `--help`: Show this message and exit.

## `bookmarker fetch`

Fetch content for the specified artifact ID.

**Usage**:

```console
$ bookmarker fetch [OPTIONS] ARTIFACT_ID
```

**Arguments**:

* `ARTIFACT_ID`: The ID of the artifact content to fetch  [required]

**Options**:

* `--help`: Show this message and exit.

## `bookmarker fetch-many`

Fetch multiple artifacts concurrently.

**Usage**:

```console
$ bookmarker fetch-many [OPTIONS] ARTIFACT_IDS...
```

**Arguments**:

* `ARTIFACT_IDS...`: The IDs of the artifact content to fetch (e.g. `1 2 3`)  [required]

**Options**:

* `--help`: Show this message and exit.

## `bookmarker summarize`

Summarize content for the specified artifact ID.

**Usage**:

```console
$ bookmarker summarize [OPTIONS] ARTIFACT_ID
```

**Arguments**:

* `ARTIFACT_ID`: The ID of the artifact content to summarize  [required]

**Options**:

* `--refresh / --no-refresh`: Force summary refresh  [default: no-refresh]
* `--help`: Show this message and exit.

## `bookmarker summarize-many`

Summarize multiple artifacts concurrently.

**Usage**:

```console
$ bookmarker summarize-many [OPTIONS] ARTIFACT_IDS...
```

**Arguments**:

* `ARTIFACT_IDS...`: The IDs of the artifact content to summarize (e.g. `1 2 3`)  [required]

**Options**:

* `--help`: Show this message and exit.
