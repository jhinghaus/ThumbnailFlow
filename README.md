# ThumbnailFlow

Generates thumbnails as data URIs in base64.

The thumbnails of a whole fs folder are created one by one
and passed to consumer on the fly. This enables the consumer to stay reactive.

There is an option for persistence to speed things up.

This packages tries to be as memory friendly as possible.
