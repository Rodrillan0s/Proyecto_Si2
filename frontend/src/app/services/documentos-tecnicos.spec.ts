import { TestBed } from '@angular/core/testing';

import { DocumentosTecnicos } from './documentos-tecnicos';

describe('DocumentosTecnicos', () => {
  let service: DocumentosTecnicos;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(DocumentosTecnicos);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
