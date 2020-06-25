'''
ARCHES - a program developed to inventory and manage immovable cultural heritage.
Copyright (C) 2013 J. Paul Getty Trust and World Monuments Fund

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.
'''

import csv
import uuid
import json
from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ObjectDoesNotExist
from arches.app.models.resource import Resource
from arches.app.models.tile import Tile

class Command(BaseCommand):
    """
    Commands for managing the loading and running of packages in Arches

    """

    def add_arguments(self, parser):

        parser.add_argument('source_csv', action='store', default=None,
            help='CSV file with the additional addresses to be added.')

    def handle(self, *args, **options):

        csv_file = options['source_csv']
        resources = {}

        # header_missing = False
        with open(csv_file, "r") as openf:
            reader = csv.DictReader(openf)
            # headers = list(reader.headers())
            # for fname in ["Resource ID", "Address", "Address Type"]:
            #     if not fname in headers:
            #         header_missing = True
            #         print(fname + " missing from CSV headers")
            # if header_missing is True:
            #     exit()

            data = [i for i in reader]

        for dp in data:

            address_type_label = dp["Address Type"].lower()
            if address_type_label == "alternative":
                address_type = "ad7fce52-1185-4ad8-bc65-e100de19be96"
            elif address_type_label == "primary":
                address_type = "b7bd2bcc-27de-4438-99c2-31bd8d07dd4c"
            else:
                print("invalid Address Type: " + str(dp["Address Type"]))
                exit()

            resid = dp["Resource ID"]

            pt = Tile.objects.filter(
                resourceinstance_id=resid,
                nodegroup_id="26730c32-943d-11e8-b3fb-94659cf754d0"
            )[0]

            if resid not in resources:
                resources[resid] = {
                    "tiles": [],
                    "resourceinstance": {
                        "resourceinstanceid": resid,
                        "graph_id": "99417385-b8fa-11e6-84a5-026d961c88e6",
                        "legacyid": resid
                    }
                }

            tile = {
                "tileid": str(uuid.uuid4()),
                "resourceinstance_id": str(pt.resourceinstance_id),
                "nodegroup_id": "2672e522-943d-11e8-8df1-94659cf754d0",
                "sortorder": 0,
                "parenttile_id": str(pt.tileid),
                "provisionaledits": None,
                "data": {
                    "2672e522-943d-11e8-8df1-94659cf754d0": dp["Address"],
                    "26733347-943d-11e8-9aaa-94659cf754d0": address_type
                }
            }

            resources[resid]["tiles"].append(tile)

        with open(csv_file.replace(".csv", ".json"), "w") as outf:
            out_data = {"business_data": {"resources": list(resources.values())}}
            json.dump(out_data, outf, indent=1)

            # nt = Tile(
            #     tileid=str(uuid.uuid4()),
            #     resourceinstance_id=pt.resourceinstance_id,
            #     nodegroup_id=pt.nodegroup_id,
            #     sortorder=0,
            #     parenttile_id=pt.tileid,
            #     provisionaledits=None,
            #     data={
            #         "2673334a-943d-11e8-ad3a-94659cf754d0": dp["Address"],
            #         "26733348-943d-11e8-a0f9-94659cf754d0": address_type
            #     }
            # )
            # print(nt.__dict__)
            # nt.save()
