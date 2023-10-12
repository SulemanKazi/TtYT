"""Utility to set up a RAG based Question Answering system for a Youtube video.

Uses Vectara for RAG, YoutubeDL for downloading subtitles.
See README.md for instructions on how to run.
"""
import argparse
import logging
import json
import os

import dl_subs
import index_subs
import query


def talk_to_yt(video_url, customer_id, corpus_id, api_key):
    subtitle_file = dl_subs.get_subtitles_for_video(video_url)
    if not subtitle_file:
        logging.error("Unable to obtain subtitles.")
        return

    indexer = index_subs.SubtitleIndexer(customer_id, api_key)
    indexer.index_file(subtitle_file, video_url, corpus_id)

    while True:
        user_input = input("Enter a query (or 'quit' to exit): ")
        if user_input.lower() == "quit":
            break
        response, _ = query.query(customer_id, corpus_id, api_key, user_input)
        print_answer(json.loads(response.text))


def print_answer(response):
    print("Summary:\n")
    print(response["responseSet"][0]["summary"][0]["text"])
    print("\n\n")
    print("Sources: \n\n")
    for i, source in enumerate(response["responseSet"][0]["response"]):
        print("[" + str(i + 1) + "]" + " " +
              source["text"].replace("\n", " ").replace("\r", ""))
        for metadata in source["metadata"]:
            print(metadata["name"] + ": " + metadata["value"])
        print("\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="Talk to YouTube",
        description="Indexes a Youtube transcript and sets up a RAG QA"
        " system using Vectara.")
    parser.add_argument("--video-url",
                        required=True,
                        help="URL of video to talk to.")
    args = parser.parse_args()

    # Get environment variables for account, corpus and api key.
    customer_id = os.environ.get("CUSTOMER_ID")
    corpus_id = os.environ.get("CORPUS_ID")
    api_key = os.environ.get("API_KEY")

    if customer_id and corpus_id and api_key:
        talk_to_yt(args.video_url, customer_id, corpus_id, api_key)
    else:
        logging.error("Environment variables not set. Please define "
                      "CUSTOMER_ID, CORPUS_ID and API_KEY for your "
                      "Vectara account.")
