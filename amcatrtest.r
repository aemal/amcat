library(amcatr)
 
aggregation_r <- function(host, token, x_axis, y_axis, filters=list()) {
  conn = amcat.connect(host, token=token)   
  
  filters = c(list(axis1=x_axis, axis2=y_axis), filters)
  d = amcat.getobjects(conn, "aggregate", filters=filters)
  
  create_js_json(d[[x_axis]], d[[y_axis]], d$count)
}

#' Create the json structure for js/highcharts from a 'sparse matrix'
#' #FIXME: assumes that x are dates and y are mediums
create_js_json <- function(x, y, v) {
  y_id = match(y, unique(y)) # simulate mediumids
  get_row <- function(xval) list(js_epoch(xval), lapply(which(x==xval), get_cell))
  js_epoch <- function(d) as.integer(as.POSIXct(d)) * 1000
  get_cell <- function(i) list(list("id"=y_id[i], "label"=y[i]), v[i])
  toJSON(lapply(unique(x), get_row))
}
