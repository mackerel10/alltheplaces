# -*- coding: utf-8 -*-
import scrapy
import re
from locations.items import GeojsonPointItem


class McDonaldsHUSpider(scrapy.Spider):

    name = "mcdonalds_hu"
    item_attributes = {"brand": "McDonald's"}
    allowed_domains = ["www.mcdonalds.hu"]
    start_urls = ("https://www.mcdonalds.hu/ettermeink",)

    def store_hours(self, data):
        day_groups = []
        this_day_group = {}
        weekdays = ["Mo", "Th", "We", "Tu", "Fr", "Sa", "Su"]
        day_hours = data.xpath(
            './/div[@class="grid__item one-half text--right"]//text()'
        ).extract()
        index = 0
        for day_hour in day_hours:
            day_hour = day_hour.strip()
            if index == 7:
                break

            hours = ""
            match = re.search(
                r"([0-9]{1,2}):([0-9]{1,2})–([0-9]{1,2}):([0-9]{1,2})", day_hour
            )
            if not match:
                hours = "off"
            else:
                sh, sm, eh, em = match.groups()
                hours = "{}:{}-{}:{}".format(
                    sh, sm, int(eh) + 12 if int(eh) < 12 else int(eh), em
                )
            short_day = weekdays[index]
            if not this_day_group:
                this_day_group = {
                    "from_day": short_day,
                    "to_day": short_day,
                    "hours": hours,
                }

            elif hours == this_day_group["hours"]:
                this_day_group["to_day"] = short_day

            elif hours != this_day_group["hours"]:
                day_groups.append(this_day_group)
                this_day_group = {
                    "from_day": short_day,
                    "to_day": short_day,
                    "hours": hours,
                }

            index = index + 1

        day_groups.append(this_day_group)

        if not day_groups:
            return None
        opening_hours = ""
        if len(day_groups) == 1 and day_groups[0]["hours"] in (
            "00:00-23:59",
            "00:00-00:00",
        ):
            opening_hours = "24/7"
        else:
            for day_group in day_groups:
                if day_group["from_day"] == day_group["to_day"]:
                    opening_hours += "{from_day} {hours}; ".format(**day_group)
                else:
                    opening_hours += "{from_day}-{to_day} {hours}; ".format(**day_group)
            opening_hours = opening_hours[:-2]

        return opening_hours

    def parse_latlon(self, data):
        map_url = (
            data.xpath('//a[@title="Mutatás a térképen"]/@href').extract_first().strip()
        )
        lat_lon = map_url.split("loc:")[1]
        lat = lat_lon.split(",")[0]
        lon = lat_lon.split(",")[1]
        return lat, lon

    def parse_store(self, response):
        address = response.xpath(
            '//h1[@class="text--uppercase"]/text()'
        ).extract_first()
        phone = response.xpath('//a[@title="Telefonszám"]/text()').extract_first()
        lat, lon = self.parse_latlon(response)

        properties = {
            "ref": response.meta["ref"],
            "phone": phone.strip() if phone else "",
            "lon": lon,
            "lat": lat,
            "name": "McDonald's",
            "addr_full": address.strip() if address else "",
        }
        opening_hours = self.store_hours(response)
        if opening_hours:
            properties["opening_hours"] = opening_hours

        yield GeojsonPointItem(**properties)

    def parse(self, response):
        results = response.xpath("//article")
        for item in results:
            ref_id = item.xpath(".//footer/a/@href").extract_first().strip()
            ref_id = ref_id.split("/")[2]
            yield scrapy.Request(
                response.urljoin("https://www.mcdonalds.hu/ettermeink/" + ref_id),
                meta={"ref": ref_id},
                callback=self.parse_store,
            )
