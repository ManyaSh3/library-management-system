from flask_restful import Resource, Api
from app import app
from models import db,Section,Book

api = Api(app)

class SectionResource(Resource):
    def get(self):
        sections=Section.query.all()
        for section in sections:
            print(section.title)
        return {'sections':[
            {
                'id':section.id,
                'title':section.title,
                'date_created': section.date_created.strftime('%Y-%m-%d'),
                'description':section.description
            } for section in sections
        ]}
    def post(self):
        pass
    def put(self):
        pass
    def delete(self):
        pass


api.add_resource(SectionResource, '/api/section')

class BookResource(Resource):
    def get(self):
        books=Book.query.all()
        for book in books:
            print(book.title)
        return {'books':[
            {
                'id':book.id,
                'title':book.title,
                'author':book.author,
                'content':book.content,
                'date_created': book.date_created.strftime('%Y-%m-%d'),
                'section_id':book.section_id
            } for book in books
        ]}
    def post(self):
        pass
    def put(self):
        pass
    def delete(self):
        pass
    
api.add_resource(BookResource, '/api/book')