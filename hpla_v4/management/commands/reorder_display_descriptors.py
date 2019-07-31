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

import uuid
from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ObjectDoesNotExist
from arches.app.models.resource import Resource
from arches.app.models.tile import Tile
from arches.app.models.graph import Graph
from arches.app.models.models import FunctionXGraph, Concept, Value, TileModel, Relation

class Command(BaseCommand):
    """
    Commands for managing the loading and running of packages in Arches

    """

    def add_arguments(self, parser):

        parser.add_argument('resourcemodel', action='store', default=None,
            help='Name of Resource Model whose display descriptor values you want to reorder.')

        parser.add_argument('--name', action='store', default=None,
            help='The label or UUID of the name type that should be pushed to the top.')

        parser.add_argument('--description', action='store', default=None,
            help='The label or UUID of the description type that should be pushed to the top.')

        parser.add_argument('--map_popup', action='store', dest=None,
            help='The label or UUID of the map_popup description type that should be pushed to the top.')

    def handle(self, *args, **options):

        graph = Graph.objects.get(name=options['resourcemodel'])

        nametype_value = self.get_value_from_input(options['name'])
        desctype_value = self.get_value_from_input(options['description'])
        popuptype_value = self.get_value_from_input(options['map_popup'])

        descriptor_function = FunctionXGraph.objects.get(
            function_id="60000000-0000-0000-0000-000000000001",
            graph=graph,
        )

        resources = Resource.objects.filter(graph_id=descriptor_function.graph_id)
        totalct = resources.count()
        print totalct, "resources to process"

        for n, resource in enumerate(resources):
            
            self.process_resource(resource, descriptor_function.config,
                nametype=nametype_value,
                desctype=desctype_value,
                popuptype=popuptype_value
            )
            
            if (n+1) % 1000 == 0:
                print n+1,
            if n+1 == totalct:
                print n+1

    def process_resource(self, resource, config, nametype=None, desctype=None, popuptype=None):

        resid = resource.resourceinstanceid
        if nametype is not None:
            self.reorder_tiles(resid, config['name']['nodegroup_id'], nametype)
        if desctype is not None:
            self.reorder_tiles(resid, config['description']['nodegroup_id'], desctype)
        if popuptype is not None:
            self.reorder_tiles(resid, config['map_popup']['nodegroup_id'], popuptype)

        resource.save()

    def reorder_tiles(self, resourceid, nodegroup, typevalue):
          
        tiles = TileModel.objects.filter(nodegroup_id=nodegroup, resourceinstance_id=resourceid).order_by("sortorder")
        
        # print "before"
        # for t in tiles:
            # print t.sortorder
        primarytileuuid = None
        for t in tiles:
            if str(typevalue.valueid) in t.data.values():
                t.sortorder = 0
                t.save()
                primarytileuuid = t.tileid
        
        # this means that the primary tile has been found and handled.
        # all other tiles must be re-saved with ascending sortorder
        if primarytileuuid is not None:
            for n, t in enumerate(tiles.exclude(tileid=primarytileuuid).order_by("sortorder")):
                t.sortorder = n+1
                t.save()
        
        # print "after"
        # for t in TileModel.objects.filter(nodegroup_id=nodegroup, resourceinstance_id=resourceid).order_by("sortorder"):
            # print t.sortorder

    def get_value_from_input(self, input):
        
        if input is None:
            return None
        
        try:
            uuid.UUID(input)
            value = Value.objects.get(valueid=input)
            return value
        except ValueError:
            pass

        values = Value.objects.filter(value=input)
        if values.count() == 0:
            print "input value '{}' not found".format(input)
            exit()
        elif values.count() > 1:
            print "multiple labels found. please choose one of the following:"
            choice_dict = {}
            for n, val in enumerate(values):
                parent_concept = Relation.objects.get(relationtype_id="member", conceptto=val.concept_id)
                parent_label = Value.objects.filter(concept_id=parent_concept.conceptfrom.conceptid)[0]
                print "{} - {} - {} --> {}".format(n+1, val.valueid, parent_label.value, val.value)
                choice_dict[str(n+1)] = val
            while True:
                choice = raw_input("choose by entering one of the numbers above: ")
                if choice in choice_dict:
                    return choice_dict[choice]
                else:
                    print "invalid choice. to quit, use ^c"
        else:
            return values[0]
