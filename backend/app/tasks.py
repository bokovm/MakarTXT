from celery import Celery
from app.services.youtube_service import YouTubeService
from app import create_app

flask_app = create_app()
celery = Celery(
    __name__, 
    broker=flask_app.config['CELERY_BROKER_URL'],
    backend=flask_app.config['CELERY_RESULT_BACKEND']
)

@celery.task(bind=True)
def download_youtube_video(self, url, format_id):
    def progress_callback(current, total):
        self.update_state(
            state='PROGRESS',
            meta={
                'progress': int((current / total) * 100),
                'speed': f"{current/(1024*1024):.1f}MB/s"
            }
        )
    
    try:
        result = YouTubeService.download_video(
            url, 
            format_id,
            progress_callback=progress_callback
        )
        return result
    except Exception as e:
        self.update_state(state='FAILURE', meta=str(e))
        raise
        
@celery.task
def download_youtube_video(url, format_id):
    from app.services.youtube_service import YouTubeService
    return YouTubeService.download_video(url, format_id)