PROGRAM_DOCUMENTS = (
    {
        'field_name': 'acte_naissance',
        'label': "Photocopie certifiée de l'Acte de naissance",
        'help_text': "Photocopie certifiée conforme de l'acte de naissance (PNG/JPG/PDF, max 5Mo)",
        'default_required': True,
    },
    {
        'field_name': 'preuve_baccalaureat',
        'label': "Preuve d'obtention du Baccalauréat",
        'help_text': "Copie du document attestant la réussite du baccalauréat ou équivalent (PNG/JPG/PDF, max 5Mo)",
        'default_required': True,
    },
    {
        'field_name': 'certificat_nationalite',
        'label': "Photocopie de la Carte Nationale d'Identité",
        'help_text': "Photocopie lisible de la Carte Nationale d'Identité (PNG/JPG/PDF, max 5Mo)",
        'default_required': True,
    },
    {
        'field_name': 'releve_notes_last_class',
        'label': 'Relevé de notes de la dernière classe fréquentée',
        'help_text': "Photocopie du relevé de notes de la dernière classe fréquentée (PNG/JPG/PDF, max 5Mo)",
        'default_required': True,
    },
    {
        'field_name': 'justificatif_dernier_diplome',
        'label': 'Photocopie de la Licence ou de tout autre diplôme équivalent',
        'help_text': "Photocopie de la Licence ou de tout autre diplôme équivalent (PNG/JPG/PDF, max 5Mo)",
        'default_required': True,
    },
    {
        'field_name': 'decharge_equivalence',
        'label': "Photocopie de la décharge de la demande d'équivalence pour les diplômes étrangers",
        'help_text': "Photocopie de la décharge de la demande d'équivalence pour les diplômes étrangers (PNG/JPG/PDF, max 5Mo)",
        'default_required': False,
    },
    {
        'field_name': 'bulletins_terminale',
        'label': 'Photocopie des bulletins de la classe de terminale',
        'help_text': "Photocopie des bulletins de la classe de terminale (PNG/JPG/PDF, max 5Mo)",
        'default_required': True,
    },
    {
        'field_name': 'releve_notes_master1',
        'label': 'Relevé de notes du Master 1 ou de tout autre diplôme équivalent',
        'help_text': "Relevé de notes du Master 1 ou de tout autre diplôme équivalent (PNG/JPG/PDF, max 5Mo)",
        'default_required': False,
    },
    {
        'field_name': 'photocopie_bts_hnd',
        'label': 'Photocopie du BTS, HND ou de tout autre diplôme équivalent',
        'help_text': "Photocopie du BTS, HND ou de tout autre diplôme équivalent (PNG/JPG/PDF, max 5Mo)",
        'default_required': False,
    },
)

PROGRAM_DOCUMENT_FIELD_NAMES = tuple(document['field_name'] for document in PROGRAM_DOCUMENTS)
PROGRAM_DOCUMENTS_BY_FIELD = {
    document['field_name']: document
    for document in PROGRAM_DOCUMENTS
}
DEFAULT_REQUIRED_PROGRAM_DOCUMENT_FIELDS = tuple(
    document['field_name']
    for document in PROGRAM_DOCUMENTS
    if document['default_required']
)