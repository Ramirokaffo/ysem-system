from django.test import TestCase

from academic.models import Program, ProgramDocumentRequirement


class ProgramDocumentRequirementTests(TestCase):
    def test_creating_program_creates_document_configuration_with_defaults(self):
        program = Program.objects.create(name='Licence Informatique')

        configuration = ProgramDocumentRequirement.objects.get(program=program)

        self.assertTrue(configuration.acte_naissance)
        self.assertTrue(configuration.preuve_baccalaureat)
        self.assertTrue(configuration.certificat_nationalite)
        self.assertTrue(configuration.releve_notes_last_class)
        self.assertTrue(configuration.justificatif_dernier_diplome)
        self.assertTrue(configuration.bulletins_terminale)
        self.assertFalse(configuration.decharge_equivalence)
        self.assertFalse(configuration.releve_notes_master1)
        self.assertFalse(configuration.photocopie_bts_hnd)
