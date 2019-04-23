from scrapy.shell import inspect_response
from scrapy.spiders import CrawlSpider
from scrapy.http import Request, FormRequest
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import Rule
import scrapy

class APHCrawler(scrapy.Spider):
    name = 'senado_crawler'
    allowed_domains = ['leyes.senado.gov.co']
    # login_page = 'http://imagelibrary.aph.org/aphb/'
    start_urls = ['http://leyes.senado.gov.co/proyectos/index.php/proyectos-ley/cuatrenio-2018-2022/2018-2019']
    page = 1
    rate = 1

    def __init__(self):
        scrapy.Spider.__init__(self)
        self.download_delay = 1/float(self.rate)

    def parse(self, response):
        print("Parse!!!")
        for year in response.css(".mega-nav.level2  a"):
            full_url = response.urljoin(year.css("::attr(href)").extract()[0])
            print("parse_year", full_url)
            req = Request(full_url, callback=self.parse_year)
            req.meta['period'] = year.css("::attr(title)").extract()[0].strip()
            yield req

    def parse_year(self, response):
        print ("Parse year**")
        # Parse images
        for href in response.css("table h3 a"):
            full_url = response.urljoin(href.css("::attr(href)").extract()[0])
            # print("Parse_law", full_url)

            req = Request(full_url, callback=self.parse_law)
            req.meta["period"] = response.meta["period"]
            yield req


        # Parse pagination
        for href in response.css(".pagination li a"):
            #Skip broken links
            if (len(href.css("::attr(href)").extract())==0): continue

            next_url = response.urljoin(href.css("::attr(href)").extract()[0])
            print("Parse pagination", next_url)
            reqNext = Request(next_url, callback=self.parse_year)
            reqNext.meta["period"] = response.meta["period"]
            yield reqNext


    def parse_law(self, response):
        self.logger.info('Parse Law %s', response.url)
        periodo = response.meta["period"]


        extractOrEmpty = lambda x: x[0].strip() if (x and len(x)>0) else ""

        res = {
            "url": response.url,
            "Periodo": periodo,
            "N-senado": extractOrEmpty(response.css("#t3-content > div.database-article.item-page > table > tbody > tr:nth-child(1) > th > dd > div > p:nth-child(1)::text").extract()),
            "Titulo": extractOrEmpty(response.css("#t3-content > div.database-article.item-page > table > tbody > tr:nth-child(1) > th > dd > div > p:nth-child(2) > big::text").extract())
        }

        for row in response.css(".block table tr"):
            tds = row.css("td")

            # Ignore empty attribs
            if (len(tds) != 2):
                continue

            attr = extractOrEmpty(tds[0].css("::text").extract())
            val = extractOrEmpty(tds[1].css("::text").extract())

            res[attr] = val


        yield res

