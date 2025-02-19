# -*- coding: utf-8 -*-
import scrapy

from locations.items import GeojsonPointItem


class BeerStoreSpider(scrapy.Spider):

    name = "beer_store"
    item_attributes = {"brand": "The Beer Store"}
    allowed_domains = ["www.thebeerstore.ca/"]
    start_urls = ("http://www.thebeerstore.ca/storelocations.json",)

    def parse(self, response):
        results = response.json()
        features = results["features"]
        for data in features:
            description = data["properties"]["description"]
            end_str = "<a href"
            properties = {
                "ref": data["properties"]["storeid"],
                "lon": data["geometry"]["coordinates"][0],
                "lat": data["geometry"]["coordinates"][1],
                "name": data["properties"]["name"],
                "addr_full": description[: description.find(end_str)],
            }

            yield GeojsonPointItem(**properties)
