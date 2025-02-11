from typing import Optional

from flask import current_app

from browse.domain.metadata import DocMetadata

from browse.services.database import get_latexml_status_for_document

import logging

def get_latexml_url (article: DocMetadata, most_recent: bool=False) -> Optional[str]:
    if not current_app.config["LATEXML_ENABLED"]:
        return None

    LATEXML_URI_BASE = current_app.config['LATEXML_BASE_URL']
    status = get_latexml_status_for_document(article.arxiv_id, article.highest_version()) if most_recent \
             else get_latexml_status_for_document(article.arxiv_id, article.version)
    logging.debug(f'{article.arxiv_id_v} version: {article.version}, highest_version: {article.highest_version()}')
    path = f'{article.arxiv_id}v{article.version}/{article.arxiv_id}v{article.version}.html'
    return f'{LATEXML_URI_BASE}/{path}' if status == 1 else None

