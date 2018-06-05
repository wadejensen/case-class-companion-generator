This script is designed to find all files within a Scala codebase which contain case classes and automatically  
generate and append a companion object which contains the names of each field in the case class as a string.  
This can be used to do psuedo type-safe access of arbitrary Columns on a DataFrame in Spark.  

Eg. if a file contained  
```
case class AliasInfo(  
    alias: String,  
    mcc_restriction: Seq[Int],  
    regex_match: Boolean,  
    source: String,  
    brand_bounded: Boolean)  
```
The result would be:

```
case class AliasInfo(  
    alias: String,  
    mcc_restriction: Seq[Int],  
    regex_match: Boolean,  
    source: String,  
    brand_bounded: Boolean)

 object AliasInfo {  
    val alias: String = "alias",  
    val mcc_restriction: String = "mcc_restriction",  
    val regex_match: String = "regex_match,  
    val source: String = "source",  
    val brand_bounded: String = "brand_bounded")
}         
```
  
 So far only the validation checks and regex match to find all files containing case classes have been written.  
 Next step is the code generation.