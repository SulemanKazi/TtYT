"""Utilites to index subtitles into Vectara."""
import logging
import json
import requests

import srt


class SubtitleIndexer:
    """Class to index subtitles into Vectara. """

    def __init__(self, customer_id, api_key, min_section_length=256):
        """Initializes the indexer.

           Args:
                customer_id: Vectara ID of the customer.
                api_key: API key for the customer.
                min_section_length: Minimum length of a subtitle section. If a
                     subtitle section is shorter than this length it is merged
                     with the next subtitle section.
            """
        self.customer_id = customer_id
        self.api_key = api_key
        self.min_section_length = min_section_length

    def index_file(self, file_path, video_title, corpus_id):
        """Given a file with SRT-format subtitles, indexes them into Vectara.

        Args:
            file_path: Path to the SRT file.
            video_title: Title of the video.
            corpus_id: Corpus ID to index into.
        """
        subs = self._process_subs_from_file(file_path)
        merged_subs = self._merge_subtitles(subs)

        return self._index_subs(corpus_id, merged_subs, video_title)

    def _index_subs(self, corpus_id, subtitles, video_title):
        """Indexes the given subtitles."""

        document = {}
        document["document_id"] = video_title

        parts = []
        for sub in subtitles:
            part = {}
            part["text"] = sub.content
            part["metadata_json"] = json.dumps({
                "start_time": str(sub.start),
                "end_time": str(sub.end),
            })
            parts.append(part)

        document["parts"] = parts

        request = {}
        request["customer_id"] = self.customer_id
        request["corpus_id"] = corpus_id
        request["document"] = document

        post_headers = {
            "x-api-key": f"{self.api_key}",
            "customer-id": f"{self.customer_id}"
        }
        response = requests.post("https://api.vectara.io/v1/core/index",
                                 timeout=30,
                                 data=json.dumps(request),
                                 verify=True,
                                 headers=post_headers)

        if response.status_code != 200:
            logging.error("Indexing failed with code %d, reason %s, text %s",
                          response.status_code, response.reason, response.text)
            return False

        return True

    def _process_subs_from_file(self, file_path):
        """Reads and processes subtitles from a file."""
        raw_subs = None
        with open(file_path, encoding="utf-8") as f:
            raw_subs = f.read()

        subs = list(srt.parse(raw_subs))
        return self._merge_subtitles(subs)

    def _merge_subtitles(self, subtitles):
        """Merges subtitle sections that are too short."""
        if len(subtitles) <= 1:
            return subtitles

        merged_subtitles = []
        buffer_sub = subtitles[0]

        for i in range(1, len(subtitles)):
            current_sub = subtitles[i]

            if len(buffer_sub.content) < self.min_section_length:
                # Append current subtitle to the previous one.
                buffer_sub = self._merge_single_sub(buffer_sub, current_sub)
            else:
                merged_subtitles.append(buffer_sub)
                buffer_sub = current_sub

        merged_subtitles.append(buffer_sub)

        return merged_subtitles

    def _merge_single_sub(self, first_sub, second_sub):
        text = first_sub.content + " " + second_sub.content
        return srt.Subtitle(index=None,
                            start=first_sub.start,
                            end=second_sub.end,
                            content=text)
