import os
from supabase import create_client
from dotenv import load_dotenv

def handler(request):
    load_dotenv()
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    supabase = create_client(url, key)

    if request.method != "POST":
        return {
            "statusCode": 405,
            "body": "Method Not Allowed"
        }
    try:
        file = request.files['file']
        user_id = request.form['user_id']
        filename = request.form['filename']
        bucket_name = "financeiro"
        path_in_bucket = f"{user_id}/{filename}"

        supabase.storage.from_(bucket_name).upload(
            path=path_in_bucket,
            file=file,
            file_options={"cache-control": "3600", "upsert": "true"}
        )

        return {
            "statusCode": 200,
            "body": {
                "message": "Upload realizado com sucesso",
                "path": path_in_bucket
            }
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "body": str(e)
        }
