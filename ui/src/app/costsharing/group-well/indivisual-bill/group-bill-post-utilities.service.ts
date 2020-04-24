import { Injectable } from '@angular/core';
import {HttpHeaders} from '@angular/common/http';
import {HttpClient} from '@angular/common/http';

interface Status {
  message: string;
  uploadStatus: boolean;
}

@Injectable({
  providedIn: 'root'
})
export class GroupBillPostUtilitiesService {

  constructor(private http: HttpClient) { }

  DeleteRequestToServer(USERNAME: string, GID: string, BID: string, MAPPEDNAME: string) {
    console.log('delete bill');
    const endpoint = 'http://127.0.0.1:5000/deleteGroupBill';
    const query = {
      username : USERNAME,
      group_id : GID,
      bill_id : BID,
      mapped_name : MAPPEDNAME
    };
    const options = {
      headers: new HttpHeaders({
        'Content-Type': 'application/json'
      }),
      body: query
    };
    return this.http.delete<Status>(endpoint, options);
  }


}